import curses

class BackgroundEngine:
    THEMES = {
        "starry night": {
            "pattern": [
                " ✦  ·    ✧     * ·    ✦   ·  ",
                "·    * ·   ✦    ·   * ·  ✦  ",
                "  ✧   ·    * ✦    ·   ✧  * ",
                "·   ✦    ·    * ·   ✦    ·   ",
                "  * ·  ✦    ·   * ·  ✦   ·",
                "✦    ·   * ·    ✦   ·    * ·"
            ],
            "color": 1  # Assumes standard color pair index
        },
        # You can append other themes from your html file here
    }

    def __init__(self, stdscr, theme_name="starry night"):
        self.stdscr = stdscr
        self.theme = self.THEMES.get(theme_name, self.THEMES["starry night"])

    def draw(self):
        max_y, max_x = self.stdscr.getmaxyx()
        for y in range(max_y):
            # Pick a line from the pattern based on y
            line = self.theme["pattern"][y % len(self.theme["pattern"])]
            # Tile it across the screen width
            row = (line * (max_x // len(line) + 1))[:max_x]
            try:
                self.stdscr.addstr(y, 0, row, curses.color_pair(self.theme["color"]))
            except curses.error:
                pass  # Ignore the bottom-right corner boundary error
