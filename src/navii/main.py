import curses
import os
import sys
from .ui import UIEngine
from .navigator import Navigator
from .background import BackgroundEngine
from .pathhandler import PathHandler
from .icons import get_icon

# =====================================================================
# 1. ARGUMENT PARSING
# =====================================================================

def parse_arguments():
    if len(sys.argv) < 2:
        return {"action": "ui", "state": "home"}

    subcommand = sys.argv[1]

    if subcommand == "cd":
        return {"action": "ui", "state": "nav"}
    elif subcommand == "jump":
        if len(sys.argv) == 2:
            return {"action": "ui", "state": "jump"}
        elif sys.argv[2] == "add":
            return {"action": "jump_add"}
        else:
            return {"action": "jump_lookup", "name": sys.argv[2]}
    elif subcommand == "memo":
        if len(sys.argv) == 2:
            return {"action": "ui", "state": "memo"}
        elif sys.argv[2] == "add":
            return {"action": "memo_add"}
        else:
            return {"action": "memo_lookup", "name": sys.argv[2]}

    return {"action": "ui", "state": "home"}


# =====================================================================
# 2. MAIN TUI LOOP
# =====================================================================

def main(stdscr, initial_state="home"):
    """
    Main controller loop for Navii.
    """
  

    ui        = UIEngine(stdscr)
    bg_engine = BackgroundEngine(stdscr)
    navigator = Navigator()

    state   = initial_state
    running = True

    while running:
        max_y, max_x = stdscr.getmaxyx()

        # ── State Logic ─────────────────────────────────────────────────────
        if state == "home":
            items      = ["cd - Directory Navigator", "jump - Saved Locations", "memo - Saved Commands"]
            current_path = "Navii Home"
            full_paths   = []

        else:   # state == "nav"
            nav_data     = navigator.list_items()
            items        = nav_data["items"]
            current_path = navigator.get_current_path()
            full_paths   = [
                os.path.join(current_path, name) if name != ".."
                else os.path.dirname(current_path)
                for name in items
            ]
            if not nav_data["success"]:
                ui.error_message = nav_data["error"]

        # ── Rendering ───────────────────────────────────────────────────────
        stdscr.erase()                        # erase() instead of clear() = less flicker
        bg_engine.draw()

        if state == "home":
            ui.draw_ui(current_path, items)
        else:
            ui.draw_cd_panel(current_path, items, full_paths, navigator.show_hidden)

        stdscr.refresh()

        # ── Input ───────────────────────────────────────────────────────────
        action = ui.get_input()

        if action == "resize":
            ui.max_y, ui.max_x = stdscr.getmaxyx()
            bg_engine.handle_resize()
            continue

        if action == "quit":
            running = False

        elif state == "home":
            if action in ("up", "down"):
                ui.move_selection(action, len(items))
            elif action == "enter":
                sel = items[ui.selection_index]
                if "cd" in sel:
                    state = "nav"
                    ui.selection_index  = 0
                    ui.scroll_position  = 0

        elif state == "nav":
            if action in ("up", "down"):
                ui.move_selection(action, len(items))

            elif action == "enter":
                if items:
                    result = navigator.go_forward(items[ui.selection_index])
                    if result["success"]:
                        ui.selection_index = 0
                        ui.scroll_position = 0
                    else:
                        ui.error_message = result["error"]

            elif action == "back":
                result = navigator.go_back()
                if result["success"]:
                    ui.selection_index = 0
                    ui.scroll_position = 0
                else:
                    ui.error_message = result["error"]

            elif action == "toggle_hidden":
                navigator.toggle_hidden()
                ui.selection_index = 0
                ui.scroll_position = 0

            elif action == "confirm":        # Space — jump here and exit
                if items:
                    sel = items[ui.selection_index]
                    if sel == "..":
                        target = os.path.dirname(current_path)
                    elif os.path.isdir(os.path.join(current_path, sel)):
                        target = os.path.join(current_path, sel)
                    else:
                        target = current_path   # Space on a file → jump to its directory
                    print(target)
                    running = False

    ui.cleanup()


# =====================================================================
# 3. ENTRY POINTS
# =====================================================================

def run_cli(args):
    # Placeholder for CLI commands (jump add, memo add, etc.)
    print(f"Executing {args['action']}...")
    sys.exit(0)


def run_tui(args):
    curses.wrapper(lambda stdscr: main(stdscr, initial_state=args["state"]))


def main_entry():
    args = parse_arguments()
    if args["action"] == "ui":
        run_tui(args)
    else:
        run_cli(args)


# =====================================================================
# 4. SCRIPT ENTRY (keep this simple — just call main_entry)
# =====================================================================

if __name__ == "__main__":
    main_entry()