import curses

def draw_smiley(stdscr):
    # Clear the screen
    stdscr.clear()
    
    # Hide the cursor
    curses.curs_set(0)
    
    # Starting coordinates for our smiley
    start_y = 5
    start_x = 10
    
    # 1. Draw the face outline using addstr and ACS line characters
    # ACS_URCORNER = Upper Right Corner, etc.
    stdscr.addch(start_y, start_x, curses.ACS_ULCORNER)
    stdscr.hline(start_y, start_x + 1, curses.ACS_HLINE, 8) # Top line
    stdscr.addch(start_y, start_x + 8, curses.ACS_URCORNER)
    
    stdscr.vline(start_y + 1, start_x, curses.ACS_VLINE, 5) # Left line
    stdscr.vline(start_y + 1, start_x + 9, curses.ACS_VLINE, 5) # Right line
    
    stdscr.addch(start_y + 6, start_x, curses.ACS_LLCORNER)
    stdscr.hline(start_y + 6, start_x + 1, curses.ACS_HLINE, 8) # Bottom line
    stdscr.addch(start_y + 6, start_x + 9, curses.ACS_LRCORNER)
    
    # 2. Draw the eyes using addstr (y, x, string)
    # Remember: y is down, x is across
    stdscr.addstr(start_y + 2, start_x + 2, "O O")
    
    # 3. Draw the nose
    stdscr.addstr(start_y + 3, start_x + 4, ">")
    
    # 4. Draw the mouth
    stdscr.addstr(start_y + 4, start_x + 2, "\\___/")
    
    # 5. Add a caption below
    stdscr.addstr(start_y + 9, start_x, "Smiley drawn purely with curses!")
    stdscr.addstr(start_y + 11, start_x, "Press 'q' to quit.")
    
    # Refresh the screen to push the drawings to the terminal
    stdscr.refresh()
    
    # Wait until the user presses 'q' to exit
    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break

if __name__ == "__main__":
    # curses.wrapper safely sets up the terminal and restores it when done
    curses.wrapper(draw_smiley)