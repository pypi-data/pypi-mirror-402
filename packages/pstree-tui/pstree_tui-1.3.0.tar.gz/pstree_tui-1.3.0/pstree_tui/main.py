#!/usr/bin/env python3
"""
Interactive process tree viewer.

Usage: pstree-tui <pattern>
       pstree-tui --restore

Example: pstree-tui claude
         pstree-tui 'python.*server'
         pstree-tui --restore   # Restore last search with all filters

Finds processes matching pattern in cmdline, then shows their
ancestors and descendants as a collapsible tree.

Controls:
  Mouse:
    Click ▶/▼     - toggle expand/collapse
    Click PID     - copy PID to clipboard
    Click row     - focus (show ancestors + children only)
  
  Keyboard:
    ↑↓            - navigate
    Enter/Space   - toggle selected node
    f             - focus selected node
    e             - expand all
    c             - collapse all
    v             - cycle view: Expanded → Paths → Collapsed
    p             - prune (hide) selected PID and descendants
    P             - restore all pruned PIDs
    s             - search (AND with current filters)
    S             - clear search filters
    k             - kill selected process (SIGTERM)
    K             - kill process tree
    m             - toggle mouse (for text selection)
    r             - refresh
    q             - quit
  
Tip: Hold Shift while selecting to bypass mouse capture
"""
import os
import re
import sys
import signal
import subprocess
import curses
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

LAST_QUERY_FILE = Path.home() / '.pstree-tui-last-query'


def save_patterns(patterns: list[str]):
    """Save patterns to file for --restore."""
    try:
        LAST_QUERY_FILE.write_text('\n'.join(patterns))
    except:
        pass


def load_patterns() -> list[str]:
    """Load patterns from file."""
    try:
        if LAST_QUERY_FILE.exists():
            patterns = [p for p in LAST_QUERY_FILE.read_text().strip().split('\n') if p]
            return patterns if patterns else []
    except:
        pass
    return []


def copy_to_clipboard(text: str):
    """Copy text to clipboard using xclip."""
    try:
        import subprocess
        subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode(), check=True)
    except:
        pass  # Silently fail if xclip not available


@dataclass
class Process:
    pid: int
    ppid: int
    comm: str
    cmdline: str
    children: list['Process'] = field(default_factory=list)
    expanded: bool = True
    matched: bool = False


def read_proc_info(pid: int) -> Optional[tuple[int, str, str]]:
    """Read ppid, comm, cmdline for a PID. Returns None if process gone."""
    try:
        with open(f'/proc/{pid}/stat', 'r') as f:
            stat = f.read()
        match = re.match(r'(\d+) \((.+)\) \S+ (\d+)', stat)
        if not match:
            return None
        ppid = int(match.group(3))
        comm = match.group(2)

        try:
            with open(f'/proc/{pid}/cmdline', 'r') as f:
                cmdline = f.read().replace('\0', ' ').strip()
        except:
            cmdline = f"[{comm}]"

        if not cmdline:
            cmdline = f"[{comm}]"

        return ppid, comm, cmdline
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return None


def get_all_processes() -> dict[int, Process]:
    """Scan /proc and return dict of pid -> Process."""
    procs = {}

    for entry in os.listdir('/proc'):
        if not entry.isdigit():
            continue
        pid = int(entry)
        info = read_proc_info(pid)
        if info:
            ppid, comm, cmdline = info
            procs[pid] = Process(pid=pid, ppid=ppid, comm=comm, cmdline=cmdline)

    return procs


def find_matching_pids(procs: dict[int, Process], patterns: list[str]) -> set[int]:
    """Find PIDs where cmdline matches ALL patterns (AND)."""
    regexes = [re.compile(p, re.IGNORECASE) for p in patterns]
    matched = set()

    for pid, proc in procs.items():
        text = proc.cmdline + " " + proc.comm
        if all(r.search(text) for r in regexes):
            matched.add(pid)
            proc.matched = True

    return matched


def get_ancestors(procs: dict[int, Process], pid: int) -> set[int]:
    """Get all ancestor PIDs up to init."""
    ancestors = set()
    current = pid

    while current in procs and current > 1:
        parent = procs[current].ppid
        if parent in procs and parent not in ancestors:
            ancestors.add(parent)
            current = parent
        else:
            break

    return ancestors


def get_descendants(procs: dict[int, Process], pid: int) -> set[int]:
    """Get all descendant PIDs recursively."""
    children_of: dict[int, list[int]] = {}
    for p in procs.values():
        children_of.setdefault(p.ppid, []).append(p.pid)

    descendants = set()
    stack = children_of.get(pid, []).copy()

    while stack:
        child = stack.pop()
        if child not in descendants:
            descendants.add(child)
            stack.extend(children_of.get(child, []))

    return descendants


def build_tree(procs: dict[int, Process], relevant_pids: set[int]) -> Optional[Process]:
    """Build tree structure from relevant PIDs. Returns root."""
    relevant = {pid: procs[pid] for pid in relevant_pids if pid in procs}

    if not relevant:
        return None

    for proc in relevant.values():
        proc.children = []

    for pid, proc in relevant.items():
        if proc.ppid in relevant:
            relevant[proc.ppid].children.append(proc)

    for proc in relevant.values():
        proc.children.sort(key=lambda p: p.pid)

    roots = [p for p in relevant.values() if p.ppid not in relevant]

    if not roots:
        return None

    if len(roots) == 1:
        return roots[0]
    else:
        fake_root = Process(pid=0, ppid=0, comm="[processes]", cmdline="[matching processes]")
        fake_root.children = sorted(roots, key=lambda p: p.pid)
        return fake_root


def flatten_tree(node: Process, depth: int = 0, excluded_pids: set[int] = None) -> list[tuple[int, Process]]:
    """Flatten tree into list of (depth, process) for display, skipping excluded PIDs."""
    if excluded_pids is None:
        excluded_pids = set()
    
    if node.pid in excluded_pids:
        return []
    
    result = [(depth, node)]

    if node.expanded:
        for child in node.children:
            result.extend(flatten_tree(child, depth + 1, excluded_pids))

    return result


class TreeUI:
    def __init__(self, stdscr, root: Process, patterns: list[str]):
        self.stdscr = stdscr
        self.root = root
        self.patterns = patterns
        self.excluded_pids = set()  # Session-only PID exclusions
        self.selected = 0
        self.scroll = 0
        self.mouse_enabled = True
        self.flash_message = None
        self.view_mode = 0  # 0=expanded, 1=paths only, 2=collapsed
        self.view_mode_names = ['Expanded', 'Paths', 'Collapsed']
        self.setup_colors()

    def setup_colors(self):
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_CYAN)
        curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        self.stdscr.bkgd(' ', curses.color_pair(1))

    def draw(self) -> list[tuple[int, Process]]:
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()

        visible = flatten_tree(self.root, excluded_pids=self.excluded_pids)
        pruned_count = len(self.excluded_pids)

        # Header
        if self.flash_message:
            header = f" {self.flash_message} "
            self.flash_message = None  # Clear after showing
        else:
            pattern_str = ' && '.join(f'/{p}/' for p in self.patterns)
            pruned_str = f" (-{pruned_count} pruned)" if pruned_count else ""
            header = f" pstree-tui: {pattern_str} ({len(visible)} nodes{pruned_str}) "
        self.stdscr.addstr(0, 0, header.ljust(w-1)[:w-1], curses.color_pair(5))

        # Buttons row
        btn_y = 1
        self.stdscr.addstr(btn_y, 1, " [E]xpand ", curses.color_pair(6))
        self.stdscr.addstr(btn_y, 12, " [C]ollapse ", curses.color_pair(6))
        self.stdscr.addstr(btn_y, 25, " [F]ocus ", curses.color_pair(6))
        self.stdscr.addstr(btn_y, 35, " [V]iew ", curses.color_pair(6))
        self.stdscr.addstr(btn_y, 44, " [S]earch ", curses.color_pair(6))
        self.stdscr.addstr(btn_y, 55, " [R]efresh ", curses.color_pair(6))

        # Tree area
        tree_start = 2
        tree_height = h - 3

        if self.selected < self.scroll:
            self.scroll = self.selected
        elif self.selected >= self.scroll + tree_height:
            self.scroll = self.selected - tree_height + 1

        for i, (depth, proc) in enumerate(visible):
            if i < self.scroll:
                continue

            screen_y = tree_start + (i - self.scroll)
            if screen_y >= h - 1:
                break

            indent = "  " * depth
            if proc.children:
                icon = "▼ " if proc.expanded else "▶ "
            else:
                icon = "  "

            max_cmd = w - len(indent) - len(icon) - 12
            cmd = proc.cmdline[:max_cmd] + "…" if len(proc.cmdline) > max_cmd else proc.cmdline
            line = f"{indent}{icon}{proc.pid:>6} {cmd}"
            line = line[:w-1].ljust(w-1)

            is_selected = (i == self.selected)
            is_matched = proc.matched

            if is_selected and is_matched:
                attr = curses.color_pair(4) | curses.A_BOLD
            elif is_selected:
                attr = curses.color_pair(3)
            elif is_matched:
                attr = curses.color_pair(2) | curses.A_BOLD
            else:
                attr = curses.color_pair(1)

            self.stdscr.addstr(screen_y, 0, line, attr)

        # Footer
        mouse_status = "Mouse:ON" if self.mouse_enabled else "Mouse:OFF"
        view_status = f"View:{self.view_mode_names[self.view_mode]}"
        footer = f" {mouse_status} | {view_status} | k:Kill | K:Tree | p:Prune | P:Restore | q:Quit "
        self.stdscr.addstr(h-1, 0, footer.ljust(w-1)[:w-1], curses.color_pair(5))

        self.stdscr.refresh()
        return visible

    def prompt_search(self) -> Optional[str]:
        """Show search prompt at bottom, return entered text or None if cancelled."""
        h, w = self.stdscr.getmaxyx()
        
        # Show prompt
        prompt = " Search (AND): "
        self.stdscr.addstr(h-1, 0, prompt.ljust(w-1)[:w-1], curses.color_pair(6))
        self.stdscr.refresh()
        
        # Enable cursor and echo
        curses.curs_set(1)
        curses.echo()
        
        # Disable mouse temporarily
        was_mouse_enabled = self.mouse_enabled
        if was_mouse_enabled:
            self.set_mouse(False)
        
        try:
            # Get input
            self.stdscr.move(h-1, len(prompt))
            input_bytes = self.stdscr.getstr(h-1, len(prompt), w - len(prompt) - 2)
            result = input_bytes.decode('utf-8').strip()
            return result if result else None
        except:
            return None
        finally:
            curses.noecho()
            curses.curs_set(0)
            if was_mouse_enabled:
                self.set_mouse(True)

    def handle_click(self, y: int, x: int, visible: list) -> Optional[str]:
        """Handle mouse click. Returns action or None."""
        h, w = self.stdscr.getmaxyx()

        if y == 1:
            if 1 <= x < 11:
                return 'expand_all'
            elif 12 <= x < 24:
                return 'collapse_all'
            elif 25 <= x < 34:
                return 'focus'
            elif 35 <= x < 43:
                return 'view'
            elif 44 <= x < 54:
                return 'search'
            elif 55 <= x < 66:
                return 'refresh'

        tree_start = 2
        tree_idx = y - tree_start + self.scroll

        if 0 <= tree_idx < len(visible):
            self.selected = tree_idx
            depth, proc = visible[tree_idx]
            
            icon_start = depth * 2
            icon_end = icon_start + 2
            pid_start = icon_end
            pid_end = pid_start + 6
            
            if icon_start <= x < icon_end and proc.children:
                proc.expanded = not proc.expanded
            elif pid_start <= x < pid_end:
                copy_to_clipboard(str(proc.pid))
                self.flash_message = f"Copied PID {proc.pid}"
            else:
                self.focus_node(proc)

        return None

    def expand_all(self, node: Process = None):
        node = node or self.root
        node.expanded = True
        for child in node.children:
            self.expand_all(child)

    def collapse_all(self, node: Process = None):
        node = node or self.root
        node.expanded = False
        for child in node.children:
            self.collapse_all(child)
        self.root.expanded = True

    def focus_node(self, target: Process):
        """Collapse all, then expand ancestors + target's children."""
        self.collapse_all()
        path = self._find_path_to(self.root, target)
        for node in path:
            node.expanded = True
        target.expanded = True

    def apply_view_mode(self):
        """Apply current view mode."""
        if self.view_mode == 0:
            self.expand_all()
        elif self.view_mode == 1:
            self.show_paths_only()
        else:
            self.collapse_all()

    def show_paths_only(self):
        """Expand only paths to matched processes, collapse everything else."""
        # First collapse all
        self.collapse_all()
        
        # Find all matched processes and expand paths to them
        matched = self._find_matched(self.root)
        for proc in matched:
            path = self._find_path_to(self.root, proc)
            for node in path:
                node.expanded = True

    def _find_matched(self, node: Process) -> list[Process]:
        """Find all matched processes in tree."""
        result = []
        if node.matched:
            result.append(node)
        for child in node.children:
            result.extend(self._find_matched(child))
        return result

    def _find_path_to(self, current: Process, target: Process, path: list = None) -> list[Process]:
        """Find path from current node to target."""
        if path is None:
            path = []
        
        path.append(current)
        
        if current is target:
            return path
        
        for child in current.children:
            result = self._find_path_to(child, target, path.copy())
            if result:
                return result
        
        return []

    def kill_process(self, proc: Process) -> bool:
        """Kill a single process with SIGTERM."""
        if proc.pid <= 1:
            self.flash_message = "Cannot kill PID 0 or 1"
            return False
        try:
            os.kill(proc.pid, signal.SIGTERM)
            self.flash_message = f"Killed PID {proc.pid}"
            return True
        except ProcessLookupError:
            self.flash_message = f"PID {proc.pid} not found"
            return False
        except PermissionError:
            self.flash_message = f"Permission denied for PID {proc.pid}"
            return False

    def kill_tree(self, proc: Process) -> bool:
        """Kill process and all descendants."""
        if proc.pid <= 1:
            self.flash_message = "Cannot kill PID 0 or 1"
            return False
        
        pids_to_kill = []
        self._collect_pids(proc, pids_to_kill)
        
        killed = 0
        failed = 0
        
        for pid in reversed(pids_to_kill):
            try:
                os.kill(pid, signal.SIGTERM)
                killed += 1
            except (ProcessLookupError, PermissionError):
                failed += 1
        
        if failed == 0:
            self.flash_message = f"Killed {killed} processes"
        else:
            self.flash_message = f"Killed {killed}, failed {failed}"
        
        return killed > 0

    def _collect_pids(self, proc: Process, pids: list):
        """Collect all PIDs in tree (parent first, then children)."""
        if proc.pid > 1:
            pids.append(proc.pid)
        for child in proc.children:
            self._collect_pids(child, pids)

    def set_mouse(self, enabled: bool):
        """Enable or disable mouse tracking."""
        self.mouse_enabled = enabled
        if enabled:
            curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
            print('\033[?1000h', end='', flush=True)
        else:
            curses.mousemask(0)
            print('\033[?1000l', end='', flush=True)

    def run(self):
        curses.curs_set(0)
        self.set_mouse(True)

        while True:
            visible = self.draw()

            try:
                key = self.stdscr.getch()
            except:
                continue

            if key == ord('q') or key == ord('Q'):
                break
            elif key == curses.KEY_UP:
                self.selected = max(0, self.selected - 1)
            elif key == curses.KEY_DOWN:
                self.selected = min(len(visible) - 1, self.selected + 1)
            elif key in (curses.KEY_ENTER, 10, 13, ord(' ')):
                if 0 <= self.selected < len(visible):
                    _, proc = visible[self.selected]
                    if proc.children:
                        proc.expanded = not proc.expanded
            elif key == ord('e') or key == ord('E'):
                self.expand_all()
                self.view_mode = 0
            elif key == ord('c') or key == ord('C'):
                self.collapse_all()
                self.view_mode = 2
            elif key == ord('f') or key == ord('F'):
                if 0 <= self.selected < len(visible):
                    _, proc = visible[self.selected]
                    self.focus_node(proc)
            elif key == ord('s'):
                # Add search filter
                new_pattern = self.prompt_search()
                if new_pattern:
                    self.patterns.append(new_pattern)
                    save_patterns(self.patterns)
                    return 'search'  # Signal to rebuild tree with new patterns
            elif key == ord('S'):
                # Clear all but first pattern
                if len(self.patterns) > 1:
                    self.patterns[:] = self.patterns[:1]
                    save_patterns(self.patterns)
                    return 'search'
            elif key == ord('v'):
                # Cycle view mode
                self.view_mode = (self.view_mode + 1) % 3
                self.apply_view_mode()
                self.flash_message = f"View: {self.view_mode_names[self.view_mode]}"
            elif key == ord('p'):
                # Prune selected node by PID
                if 0 <= self.selected < len(visible):
                    _, proc = visible[self.selected]
                    if proc.pid > 0:
                        self.excluded_pids.add(proc.pid)
                        self.flash_message = f"Pruned PID {proc.pid}"
                        if self.selected > 0:
                            self.selected -= 1
            elif key == ord('P'):
                # Clear all pruned PIDs
                count = len(self.excluded_pids)
                self.excluded_pids.clear()
                self.flash_message = f"Restored {count} pruned PIDs"
            elif key == ord('k'):
                if 0 <= self.selected < len(visible):
                    _, proc = visible[self.selected]
                    self.kill_process(proc)
            elif key == ord('K'):
                if 0 <= self.selected < len(visible):
                    _, proc = visible[self.selected]
                    self.kill_tree(proc)
            elif key == ord('m') or key == ord('M'):
                self.set_mouse(not self.mouse_enabled)
            elif key == ord('r') or key == ord('R'):
                return 'refresh'
            elif key == curses.KEY_MOUSE and self.mouse_enabled:
                try:
                    _, mx, my, _, state = curses.getmouse()
                    if state & (curses.BUTTON1_CLICKED | curses.BUTTON1_PRESSED):
                        action = self.handle_click(my, mx, visible)
                        if action == 'expand_all':
                            self.expand_all()
                            self.view_mode = 0
                        elif action == 'collapse_all':
                            self.collapse_all()
                            self.view_mode = 2
                        elif action == 'focus':
                            if 0 <= self.selected < len(visible):
                                _, proc = visible[self.selected]
                                self.focus_node(proc)
                        elif action == 'view':
                            self.view_mode = (self.view_mode + 1) % 3
                            self.apply_view_mode()
                            self.flash_message = f"View: {self.view_mode_names[self.view_mode]}"
                        elif action == 'search':
                            new_pattern = self.prompt_search()
                            if new_pattern:
                                self.patterns.append(new_pattern)
                                save_patterns(self.patterns)
                                return 'search'
                        elif action == 'refresh':
                            return 'refresh'
                except:
                    pass

        self.set_mouse(False)
        return 'quit'


def main(stdscr, patterns: list[str]):
    while True:
        procs = get_all_processes()
        matched_pids = find_matching_pids(procs, patterns)

        if not matched_pids:
            stdscr.clear()
            pattern_str = ' && '.join(patterns)
            stdscr.addstr(0, 0, f"No processes matching '{pattern_str}' found. Press q to quit, S to clear filters.")
            stdscr.refresh()
            while True:
                key = stdscr.getch()
                if key == ord('q'):
                    save_patterns(patterns)
                    return
                elif key == ord('S') and len(patterns) > 1:
                    patterns[:] = patterns[:1]
                    break
            continue

        relevant = set(matched_pids)
        for pid in matched_pids:
            relevant |= get_ancestors(procs, pid)
            relevant |= get_descendants(procs, pid)

        root = build_tree(procs, relevant)
        if not root:
            stdscr.clear()
            stdscr.addstr(0, 0, "Could not build tree. Press q to quit.")
            stdscr.refresh()
            while stdscr.getch() != ord('q'):
                pass
            save_patterns(patterns)
            return

        ui = TreeUI(stdscr, root, patterns)
        result = ui.run()

        if result == 'quit':
            save_patterns(patterns)
            break
        # 'refresh' or 'search' continues the loop


def cli():
    """Entry point for the CLI."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    if sys.argv[1] == '--restore':
        patterns = load_patterns()
        if not patterns:
            print("No saved query to restore. Use: pstree-tui <pattern>")
            sys.exit(1)
        print(f"Restoring: {' && '.join(patterns)}")
    else:
        patterns = [sys.argv[1]]
    
    curses.wrapper(lambda stdscr: main(stdscr, patterns))


if __name__ == "__main__":
    cli()