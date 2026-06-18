import curses

class UIEngine:
    def __init__(self, stdscr):
        # ESSENTIAL - Curses setup
        self.stdscr = stdscr
        
        # ESSENTIAL - Terminal info
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        
        # ESSENTIAL - Colors
        curses.start_color()
        self.WHITE = 1
        self.CYAN = 2
        self.YELLOW = 3
        curses.init_pair(self.WHITE, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(self.CYAN, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(self.YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        
        # ESSENTIAL - Terminal settings
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)

        self.selection_index = 0
        self.scroll_position = 0

        self.SELECTION = 4
        curses.init_pair(self.SELECTION, curses.COLOR_BLACK, curses.COLOR_CYAN)

        self.error_message = None

    def cleanup(self):
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    def refresh(self):
        self.stdscr.refresh()
    
    def map_key(self, key):
        # CONVERTS USER KEY INPUT INTO ACTION 
        # Up
        if key == curses.KEY_UP or key == ord("k") or key == 450:
            return "up"
        # Down
        elif key == curses.KEY_DOWN or key == ord("j") or key == 456:
            return "down"
        # Left / Go back
        elif key == curses.KEY_LEFT or key == ord("h") or key == curses.KEY_BACKSPACE or key == ord('\b') or key == 452:
            return "back"
        # Right / Enter directory
        elif key == curses.KEY_RIGHT or key == ord("l") or key == ord('\n') or key == 454:
            return "enter"
        # Confirm selection
        elif key == ord(' '):
            return "confirm"
        # Toggle hidden files
        elif key == ord('.'):
            return "toggle_hidden"
        # Quit
        elif key == 27 or key == ord('q'):
            return "quit"
        elif key == curses.KEY_RESIZE:
            return "resize"
        else:
            return None  # Unknown key
        

    def get_input(self):
        # GET INPUT AND RETURN ACTION NAME
        key = self.stdscr.getch()
        return self.map_key(key)
    
    def move_selection(self, direction, total_items):
        """Move selection up/down and auto-scroll to keep it visible"""
        if direction == "down":
            self.selection_index = min(self.selection_index + 1, total_items - 1)
        elif direction == "up":
            self.selection_index = max(self.selection_index - 1,0)
        # Auto-scroll to keep selection visible
        viewport_height = self.max_y - 3  # Account for header/footer
        self.scroll_position = max(0, self.selection_index - viewport_height // 2)

    def draw_list(self, items, start_row=1):
        """Draw list of items with selection highlight"""
        viewport_height = self.max_y - 3
    
        for i, item in enumerate(items[self.scroll_position:self.scroll_position + viewport_height]):
            row = start_row + i
            if self.scroll_position + i == self.selection_index:
                self.stdscr.addstr(row, 0, item, curses.color_pair(self.SELECTION))
            else:
                self.stdscr.addstr(row, 0, item, curses.color_pair(self.WHITE))

    def draw_ui(self, current_path, items):

        # Draw header: Current Path
        self.stdscr.addstr(0, 0, current_path, curses.color_pair(self.CYAN))

        # LIST ITEMS
        self.draw_list(items, start_row=1)

        # Footer: Keybindings
        footer_text = "↑↓/[k][j]: Navigate | Enter[l]: Open | ⌫ Backspace: Go Back | q: Quit"
        try:
            self.stdscr.addstr(self.max_y - 1, 0, footer_text, curses.color_pair(self.YELLOW))
        except curses.error:
            pass
        
        # If there's an error message, display it above the footer
        if self.error_message:
            self.stdscr.addstr(self.max_y - 2, 0, f"Error: {self.error_message}", curses.color_pair(self.YELLOW))


