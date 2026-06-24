import curses
import random

class BackgroundEngine:
    STAR_CHARS = ['✦', '✧', '*', '·', '◇']
    STAR_CHARS_ASCII = ['+', '*', '.', ',', ' ']  # fallback for basic terminals
    THEMES = {
        "starry night": {
            "star_density": 0.04,   # 4% of all cells will have a star
            "star_color_pairs": [5, 6, 7],  # bright, mid, dim
            "city_color_pair": 8,           # dark silhouette
            "glow_color_pair": 9,           # horizon glow
            "window_color_pairs": [10, 11]  # NEW: warm yellow/white for lit windows
        }
    }

    def __init__(self, stdscr, theme_name="starry night"):
        self.stdscr = stdscr
        self.theme = self.THEMES.get(theme_name, self.THEMES["starry night"])
        self.YELLOW = 3
        self.max_y, self.max_x = stdscr.getmaxyx()
        self.ascii_mode = False
        self._generate(self.max_y, self.max_x)

    def _detect_unicode(self):
        """Try rendering a unicode char — fall back to ASCII if it fails"""
        try:
            self.stdscr.addstr(0, 0, '✦')
            self.ascii_mode = False
        except:
            self.ascii_mode = True

    def _generate(self, rows, cols):
        """Pre-calculate all static background elements (Stars + City)"""
        self._detect_unicode()
        chars = self.STAR_CHARS_ASCII if self.ascii_mode else self.STAR_CHARS
        total_cells = rows * cols
        star_count = int(total_cells * self.theme["star_density"])
        sky_rows = int(rows * 0.80)

        # 1. Generate Stars
        self.stars = []
        for _ in range(star_count):
            y = random.randint(0, sky_rows - 1)
            x = random.randint(0, cols - 2) 
            char = random.choices(
                chars,
                weights=[1, 2, 4, 6, 3], 
                k=1
            )[0]
            brightness = random.choice(self.theme["star_color_pairs"])
            self.stars.append((y, x, char, brightness))

        # 2. Generate City and Windows
        self.city_cells = []
        building_pattern = [6, 10, 4, 12, 7, 9, 5, 11, 8, 6, 10, 4, 7, 9, 5]
        pattern_width = 5 
        city_color = self.theme["city_color_pair"]
        window_colors = self.theme["window_color_pairs"]

        for col in range(0, cols - 1, pattern_width):
            building_idx = (col // pattern_width) % len(building_pattern)
            height = building_pattern[building_idx]
            
            start_col = col
            end_col = min(col + pattern_width - 1, cols - 1)

            for row_offset in range(height):
                row = rows - 1 - row_offset
                if row < 0 or row >= rows:
                    continue

                for c in range(start_col, end_col):
                    char = '█' if row_offset > 0 else '▄'
                    color = city_color

                    # --- Window Logic ---
                    # Keep edges solid to maintain building shape
                    is_interior_row = 1 < row_offset < height - 1
                    is_interior_col = start_col < c < end_col - 1

                    # Create a grid pattern (every other row and column)
                    if is_interior_row and is_interior_col and row_offset % 2 == 0 and c % 2 != 0:
                        # 25% chance for a window to be "lit"
                        if random.random() < 0.25:
                            color = random.choice(window_colors)
                            char = '█' if not self.ascii_mode else '#'

                    self.city_cells.append((row, c, char, color))

    def _draw_stars(self):
        for (y, x, char, color_pair) in self.stars:
            try:
                self.stdscr.addstr(y, x, char, curses.color_pair(color_pair))
            except curses.error:
                pass

    def _draw_city(self):
        """Draw detailed buildings with windows along the bottom"""
        rows, cols = self.stdscr.getmaxyx()

        # Define distinct buildings: (width, height, window_char)
        # Each building is a dict with its own character style
        buildings = [
            {"w": 8,  "h": 14, "win": "▓"},
            {"w": 5,  "h": 8,  "win": "·"},
            {"w": 12, "h": 20, "win": "▪"},
            {"w": 6,  "h": 10, "win": ""},
            {"w": 15, "h": 25, "win": "░"},
            {"w": 7,  "h": 12, "win": "·"},
            {"w": 10, "h": 18, "win": "█"},
            {"w": 5,  "h": 7,  "win": "·"},
            {"w": 11, "h": 22, "win": "▪"},
            {"w": 6,  "h": 9,  "win": "·"},
            {"w": 9,  "h": 16, "win": "█"},
            {"w": 4,  "h": 6,  "win": "·"},
            {"w": 13, "h": 21, "win": "▪"},
            {"w": 7,  "h": 11, "win": "·"},
            {"w": 8,  "h": 15, "win": "█"},
        ]

        # Tile buildings across the screen width
        col = 0
        b_idx = 0
        while col < cols - 1:
            b = buildings[b_idx % len(buildings)]
            w = min(b["w"], cols - col - 1)
            h = b["h"]
            b_idx += 1

            for row_offset in range(h):
                row = rows - 1 - row_offset
                if row < 0 or row >= rows - 1:
                    continue

                if row_offset == 0:
                    # Ground floor — solid base
                    line = '▀' * w
                    try:
                        self.stdscr.addstr(row, col, line, curses.color_pair(8) | curses.A_BOLD)
                    except curses.error:
                        pass

                elif row_offset == h - 1:
                    # Rooftop row
                    roof = '▄' + '─' * (w - 2) + '▄' if w > 2 else '▄' * w
                    try:
                        self.stdscr.addstr(row, col, roof, curses.color_pair(8) | curses.A_BOLD)
                    except curses.error:
                        pass

                else:
                    # Middle floors — walls with windows
                    floor_line = list('█' * w)

                    # Place windows every 2 chars, starting at col 1, skip last col
                    for wc in range(1, w - 1, 2):
                        # Randomly light some windows (dim = off, bold = on)
                        # Use row+col as seed so windows stay stable between redraws
                        lit = (row * 7 + (col + wc) * 3) % 5 != 0
                        floor_line[wc] = b["win"]

                    try:
                        # Draw wall base
                        self.stdscr.addstr(row, col, ''.join(floor_line), curses.color_pair(8))
                        # Re-draw lit windows on top in yellow/dim
                        for wc in range(1, w - 1, 2):
                            lit = (row * 7 + (col + wc) * 3) % 5 != 0
                            win_color = curses.color_pair(self.YELLOW) if lit else curses.color_pair(8) | curses.A_DIM
                            self.stdscr.addstr(row, col + wc, b["win"], win_color)
                    except curses.error:
                        pass

            # 1-char gap between buildings
            col += b["w"] + 1

    def _draw_glow(self):
        """Draw a subtle horizon glow just above the tallest building"""
        rows, cols = self.stdscr.getmaxyx()
        tallest = 25  # matches tallest building height above
        glow_row = rows - tallest - 2

        if glow_row >= 0:
            for c in range(0, cols - 1):
                # Alternate chars for a more organic glow line
                char = '▁' if c % 3 == 0 else ' '
                try:
                    self.stdscr.addstr(glow_row, c, char, curses.color_pair(9) | curses.A_DIM)
                except curses.error:
                    pass

    def draw(self):
        self._draw_stars()
        self._draw_glow()  # Drawn before city so city overlaps it
        self._draw_city()

    def handle_resize(self):
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        self._generate(self.max_y, self.max_x)