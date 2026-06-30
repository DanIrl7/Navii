import curses
import random


# ══════════════════════════════════════════════════════════════════════════════
# SKY THEME REGISTRY
# Each entry defines everything the sky renderer needs.
# color_pairs: [bright, mid, dim] — referenced by index into UIEngine's pairs
# particle_chars / ascii_chars: what gets scattered across the sky
# particle_weights: probability weights matching particle_chars order
# glow_pair: color pair for the horizon glow line
# glow_char: character used for the glow row
# density: fraction of sky cells that get a particle
# ══════════════════════════════════════════════════════════════════════════════
SKY_THEMES = {
    "starry night": {
        "label":            "Starry Night",
        "color_pairs":      [5, 6, 7],
        "glow_pair":        9,
        "glow_char":        "▁",
        "density":          0.04,
        "particle_chars":   ["✦", "✧", "*", "·", "◇", "★", "☆"],
        "ascii_chars":      ["+", "*", ".", ",", "o", "x", " "],
        "particle_weights": [1, 2, 3, 8, 4, 1, 2],
    },
    "vaporwave": {
        "label":            "Vaporwave",
        "color_pairs":      [13, 14, 15],
        "glow_pair":        17,
        "glow_char":        "─",
        "density":          0.035,
        "particle_chars":   ["◆", "◇", "▪", "·", "░", "▫", "★"],
        "ascii_chars":      ["#", "+", ".", "-", ":", ".", " "],
        "particle_weights": [2, 3, 4, 8, 2, 3, 1],
    },
    "matrix": {
        "label":            "Matrix",
        "color_pairs":      [18, 19, 20],
        "glow_pair":        22,
        "glow_char":        "▄",
        "density":          0.06,
        "particle_chars":   ["0", "1", "│", "┃", "╎", "╏", "▓", "░", "▒"],
        "ascii_chars":      ["0", "1", "|", "!", ":", ".", "#"],
        "particle_weights": [3, 3, 2, 2, 2, 4, 1, 1, 1],
    },
    "sunset": {
        "label":            "Sunset",
        "color_pairs":      [23, 24, 25],
        "glow_pair":        26,
        "glow_char":        "▀",
        "density":          0.025,
        "particle_chars":   ["~", "≈", "─", "∼", "⌒", "v", "ʌ"],
        "ascii_chars":      ["~", "=", "-", "~", "^", "v", " "],
        "particle_weights": [4, 3, 3, 3, 2, 2, 1],
    },
    "rainy day": {
        "label":            "Rainy Day",
        "color_pairs":      [27, 28, 29],
        "glow_pair":        30,
        "glow_char":        "░",
        "density":          0.07,
        "particle_chars":   ["│", "╎", "╏", "┊", "┋", "·", "╷"],
        "ascii_chars":      ["|", "|", ":", ".", "'", ",", "`"],
        "particle_weights": [4, 3, 3, 2, 2, 4, 1],
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# GROUND THEME REGISTRY
# Each entry defines everything the ground renderer needs.
# color_pair: main ground/structure color
# accent_pair: secondary color (windows, leaves, waves, etc.)
# highlight_pair: brightest accent (lit windows, foam, flowers, etc.)
# layers: list of row descriptors drawn bottom-up.
#   Each layer is a dict:
#     "h": int        — how many terminal rows tall this layer is
#     "chars": str    — characters tiled across the row (cycled left-to-right)
#     "color": str    — "main", "accent", or "highlight"
#     "bold": bool    — whether to apply A_BOLD
#     "dim": bool     — whether to apply A_DIM
# detail_fn: string key — which detail-drawing function to call on top
#   (None, "city_windows", "forest_canopy", "ocean_waves", "beach_surf",
#    "ranch_fence")
# tallest: int — used to position the glow row above the ground
# ══════════════════════════════════════════════════════════════════════════════
GROUND_THEMES = {
    "city": {
        "label":          "City Skyscrapers",
        "color_pair":     8,
        "accent_pair":    3,    # yellow windows
        "highlight_pair": 11,   # white office light
        "detail_fn":      "city_windows",
        "tallest":        25,
        "buildings": [
            {"w": 8,  "h": 14, "win": "▓"},
            {"w": 5,  "h": 8,  "win": "·"},
            {"w": 12, "h": 20, "win": "▪"},
            {"w": 6,  "h": 10, "win": "░"},
            {"w": 15, "h": 25, "win": "░"},
            {"w": 7,  "h": 12, "win": "·"},
            {"w": 10, "h": 18, "win": "▪"},
            {"w": 5,  "h": 7,  "win": "·"},
            {"w": 11, "h": 22, "win": "▓"},
            {"w": 6,  "h": 9,  "win": "·"},
            {"w": 9,  "h": 16, "win": "▪"},
            {"w": 4,  "h": 6,  "win": "·"},
            {"w": 13, "h": 21, "win": "░"},
            {"w": 7,  "h": 11, "win": "·"},
            {"w": 8,  "h": 15, "win": "▓"},
        ],
    },

    # ────────────────────────────────────────────────────────────────────
    # BEACH — reworked. Instead of flat repeating-character bands, the
    # beach now has a textured (non-tiled) sand bed, a proper foam/surf
    # transition, and scattered props: two palm trees, a beach umbrella
    # + towel, a crab, and a few shells. Gulls are drawn in the sky pass
    # so they sit correctly above the horizon glow.
    #
    # Reference style notes (adapted, not copied, from classic beach/palm
    # ASCII art such as the pieces archived at asciiart.eu / Joan Stark's
    # collection): palm trees as a leaning trunk of slashes topped with a
    # simple frond crown, and a crab as a compact claw-body-claw glyph —
    # kept intentionally small and original rather than reproducing any
    # specific existing piece.
    # ────────────────────────────────────────────────────────────────────
    "beach": {
        "label":          "Beach",
        "color_pair":     31,   # sand
        "accent_pair":    32,   # ocean
        "highlight_pair": 33,   # foam / white
        "detail_fn":      "beach_surf",
        "tallest":        9,
        # Fallback flat layers — used by the generic _draw_layers() path
        # only if the terminal is too small to safely place props.
        "layers": [
            {"h": 2, "chars": "▒░▒▒░▒░▒▒░",          "color": "main",      "bold": True,  "dim": False},  # sand
            {"h": 1, "chars": "≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈ ~", "color": "highlight", "bold": True,  "dim": False},  # foam
            {"h": 2, "chars": "≋≈≋≈≋≈≋≈≋≈",           "color": "accent",    "bold": False, "dim": False},  # surf
            {"h": 2, "chars": "~ ≈ ~ ≈ ~ ≈ ~ ≈ ~ ≈", "color": "accent",    "bold": False, "dim": True },  # open water
        ],
        # Prop layout, positioned proportionally so it scales with width.
        "palms":    [{"x_frac": 0.10, "lean": -1, "h": 3},
                     {"x_frac": 0.88, "lean": 1,  "h": 3}],
        "umbrella": {"x_frac": 0.32},
        "crab":     {"x_frac": 0.58},
        "shells":   [0.20, 0.45, 0.70, 0.78],
        "gulls":    [{"x_frac": 0.40, "row_from_top": 1},
                     {"x_frac": 0.60, "row_from_top": 3},
                     {"x_frac": 0.75, "row_from_top": 0}],
    },

    "forest": {
        "label":          "Forest",
        "color_pair":     34,   # dark green
        "accent_pair":    35,   # mid green
        "highlight_pair": 36,   # bright green / yellow-green
        "detail_fn":      "forest_canopy",
        "tallest":        18,
        "layers": [
            {"h": 2, "chars": "████████████",                    "color": "main",      "bold": True,  "dim": False},
            {"h": 3, "chars": "▓██▓██▓██▓██",                   "color": "main",      "bold": False, "dim": False},
            {"h": 3, "chars": "▒▓█▒▓█▒▓█▒▓█",                  "color": "accent",    "bold": False, "dim": False},
            {"h": 4, "chars": " T T T T T T T T T T ",          "color": "accent",    "bold": True,  "dim": False},
            {"h": 3, "chars": "/T\\ /T\\ /T\\ /T\\ /T\\",      "color": "highlight", "bold": False, "dim": False},
            {"h": 3, "chars": "^^^^^^^^^^^^^^^^^^^^^^^^^^^",     "color": "highlight", "bold": True,  "dim": False},
        ],
    },
    "ranch": {
        "label":          "Ranch",
        "color_pair":     37,   # brown/tan ground
        "accent_pair":    38,   # wood fence / barn red
        "highlight_pair": 39,   # sky-touching grass green
        "detail_fn":      "ranch_fence",
        "tallest":        10,
        "layers": [
            {"h": 2, "chars": "▓▓▓▓▓▓▓▓▓▓▓▓",                  "color": "main",      "bold": True,  "dim": False},
            {"h": 2, "chars": "▒▒▒▒▒▒▒▒▒▒▒▒",                  "color": "main",      "bold": False, "dim": False},
            {"h": 1, "chars": "─┤ ├─┤ ├─┤ ├─┤ ├─",             "color": "accent",    "bold": True,  "dim": False},
            {"h": 1, "chars": " │   │   │   │   │ ",            "color": "accent",    "bold": False, "dim": False},
            {"h": 1, "chars": "─┤ ├─┤ ├─┤ ├─┤ ├─",             "color": "accent",    "bold": True,  "dim": False},
            {"h": 1, "chars": " │   │   │   │   │ ",            "color": "accent",    "bold": False, "dim": False},
            {"h": 2, "chars": ".,.,.,wWwWw.,.,.,wWwWw",         "color": "highlight", "bold": False, "dim": False},
        ],
    },
    "ocean": {
        "label":          "Ocean",
        "color_pair":     40,   # deep blue
        "accent_pair":    41,   # mid blue
        "highlight_pair": 42,   # white foam / bright
        "detail_fn":      "ocean_waves",
        "tallest":        10,
        "layers": [
            {"h": 2, "chars": "████████████",                    "color": "main",      "bold": True,  "dim": False},
            {"h": 2, "chars": "▓▓▓▓▓▓▓▓▓▓▓▓",                  "color": "main",      "bold": False, "dim": False},
            {"h": 2, "chars": "≋≋≈≋≋≈≋≋≈≋≋≈",                  "color": "accent",    "bold": False, "dim": False},
            {"h": 2, "chars": "≈ ~ ≈ ~ ≈ ~ ≈ ~",               "color": "accent",    "bold": True,  "dim": False},
            {"h": 2, "chars": "~ ≋ ~ ≋ ~ ≋ ~ ≋",               "color": "highlight", "bold": True,  "dim": False},
        ],
    },
}


# Fallback glyphs for beach props when the terminal can't render the
# preferred unicode character (used only in ascii_mode).
_BEACH_ASCII_FALLBACK = {
    "≈": "~", "≋": "~", "▒": ".", "░": ".", "▓": "#",
    "⋆": "*", "˚": ".", "∘": "o",
}


# ══════════════════════════════════════════════════════════════════════════════
# SCENE THEME REGISTRY
#
# A "scene" is a third background mode, separate from sky+ground: it is one
# unified full-screen composition rather than a stacked sky layer + ground
# layer. Used for backgrounds that don't decompose cleanly into "sky on top,
# ground on bottom" — e.g. a centered sun whose glow spans both halves of
# the screen, with a foreground element (palm tree) breaking across the
# horizon line.
#
# Each scene theme defines:
#   color_pairs: dict of named curses pair ids used by this scene
#   build_fn:    string key naming which _build_<x>_scene() method lays out
#                the character/color grids for this scene
# ══════════════════════════════════════════════════════════════════════════════
SCENE_THEMES = {
    "vaporwave sunset": {
        "label":       "Vaporwave Sunset",
        "build_fn":    "vaporwave_sunset",
        # Color roles -> curses pair ids (wired up in UIEngine, see notes below)
        "pairs": {
            "sky_dim":    50,   # faint blue sky texture
            "sky_mid":    51,   # mid blue / cyan
            "sun_core":   52,   # bright pink/white sun center
            "sun_mid":    53,   # magenta sun body
            "sun_edge":   54,   # deep pink sun edge
            "horizon":    55,   # pink horizon line
            "water":      56,   # blue water/reflection
            "water_glow": 57,   # pink reflection under the sun
            "palm":       58,   # dark magenta/blue palm silhouette
        },
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# BACKGROUND ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class BackgroundEngine:

    def __init__(self, stdscr,
                 sky_theme="starry night",
                 ground_theme="city",
                 sky_enabled=True,
                 ground_enabled=True,
                 mode="layered",
                 scene_theme="vaporwave sunset"):
        """
        mode: "layered" (default, original sky+ground stacking) or
              "scene" (single unified full-screen background, e.g.
              vaporwave sunset). When mode="scene", sky_enabled and
              ground_enabled are ignored — the scene always draws as
              one composition.
        """
        self.stdscr       = stdscr
        self.sky_enabled    = sky_enabled
        self.ground_enabled = ground_enabled
        self.ascii_mode     = False
        self.max_y, self.max_x = stdscr.getmaxyx()
        self.frame = 0  # increments each draw() call; drives animation

        self.mode = mode if mode in ("layered", "scene") else "layered"
        self._set_scene(scene_theme)

        self._set_sky(sky_theme)
        self._set_ground(ground_theme)
        self._generate()

    # ── Theme setters ──────────────────────────────────────────────────────

    def _set_sky(self, name):
        self.sky_name  = name
        self.sky_theme = SKY_THEMES.get(name, SKY_THEMES["starry night"])

    def _set_ground(self, name):
        self.ground_name  = name
        self.ground_theme = GROUND_THEMES.get(name, GROUND_THEMES["city"])

    def _set_scene(self, name):
        self.scene_name  = name
        self.scene_theme = SCENE_THEMES.get(name, SCENE_THEMES["vaporwave sunset"])

    def set_sky(self, name):
        """Switch sky theme and regenerate."""
        self._set_sky(name)
        self._generate()

    def set_ground(self, name):
        """Switch ground theme and regenerate."""
        self._set_ground(name)
        self._generate()

    def set_scene(self, name):
        """Switch scene theme (used in mode='scene') and regenerate."""
        self._set_scene(name)
        self._generate()

    def set_mode(self, mode):
        """Switch between 'layered' (sky+ground) and 'scene' (unified)."""
        if mode in ("layered", "scene"):
            self.mode = mode
            self._generate()

    def set_sky_enabled(self, enabled):
        self.sky_enabled = enabled

    def set_ground_enabled(self, enabled):
        self.ground_enabled = enabled

    # ── Unicode detection ──────────────────────────────────────────────────

    def _detect_unicode(self):
        try:
            self.stdscr.addstr(0, 0, "✦")
            self.ascii_mode = False
        except curses.error:
            self.ascii_mode = True

    # ── Pre-generation ─────────────────────────────────────────────────────

    def _generate(self):
        """Pre-calculate static layout. In 'layered' mode this builds sky
        particles and (for beach) prop positions. In 'scene' mode it
        builds the unified scene grid instead."""
        self._detect_unicode()
        rows, cols = self.max_y, self.max_x

        if self.mode == "scene":
            self._generate_scene(rows, cols)
            return

        sky  = self.sky_theme
        chars = sky["ascii_chars"] if self.ascii_mode else sky["particle_chars"]
        weights = sky["particle_weights"][:len(chars)]

        sky_rows    = int(rows * 0.75)
        total_cells = max(1, sky_rows * cols)
        count       = int(total_cells * sky["density"])

        self.particles = []
        for _ in range(count):
            y    = random.randint(0, max(0, sky_rows - 1))
            x    = random.randint(0, max(0, cols - 2))
            char = random.choices(chars, weights=weights, k=1)[0]
            pair = random.choice(sky["color_pairs"])
            self.particles.append((y, x, char, pair))

        if self.ground_name == "beach":
            self._generate_beach_props(rows, cols)

    def _generate_scene(self, rows, cols):
        """Dispatch to the right scene builder based on scene_theme."""
        build_fn = self.scene_theme.get("build_fn")
        builders = {
            "vaporwave_sunset": self._build_vaporwave_sunset,
        }
        builder = builders.get(build_fn, self._build_vaporwave_sunset)
        self.scene_grid = builder(rows, cols)

    def _build_vaporwave_sunset(self, rows, cols):
        """
        Build the vaporwave beach-sunset scene as a grid of (char, pair_key)
        tuples. pair_key is a string looked up against scene_theme["pairs"]
        at draw time, so color assignment stays data-driven.

        Layout: sky texture (top) -> centered sun with horizontal scanline
        gaps (vaporwave signature) sitting on the horizon -> reflective
        water with vertical streaks under the sun -> a foreground palm
        tree silhouette breaking across the horizon on the right side.
        """
        import math

        grid = [[(' ', None) for _ in range(cols)] for _ in range(rows)]

        horizon_row = int(rows * 0.66)
        sun_cx = cols // 2
        sun_cy = horizon_row - max(1, int(rows * 0.07))
        sun_r  = max(3, int(min(cols * 0.22, rows * 0.5)))
        density_chars = " .:-=+*#%@"

        def put(y, x, ch, pair_key):
            if 0 <= y < rows and 0 <= x < cols:
                grid[y][x] = (ch, pair_key)

        # --- Sun: concentric density rings with horizontal scanline gaps
        for y in range(rows):
            for x in range(cols):
                dx = x - sun_cx
                dy = (y - sun_cy) * 2.1  # character aspect correction
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= sun_r:
                    if y % 3 == 0 and dist > sun_r * 0.3:
                        continue  # scanline gap — the vaporwave stripe look
                    t = 1 - (dist / sun_r)
                    idx = min(len(density_chars) - 1, int(t * (len(density_chars) - 1)))
                    idx = max(2, idx)
                    pair_key = "sun_core" if t > 0.7 else ("sun_mid" if t > 0.35 else "sun_edge")
                    put(y, x, density_chars[idx], pair_key)

        # --- Sky texture: sparse, denser near the horizon, sparser near top
        rng = random.Random(rows * 9176 + cols)  # stable per terminal size
        for y in range(0, horizon_row):
            density = (y / max(1, horizon_row)) * 0.045
            pair_key = "sky_mid" if y > horizon_row * 0.5 else "sky_dim"
            for x in range(cols):
                if grid[y][x][0] == ' ' and rng.random() < density:
                    put(y, x, rng.choice([".", "·", ":"]), pair_key)

        # --- Horizon line
        for x in range(cols):
            if grid[horizon_row][x][0] == ' ':
                put(horizon_row, x, '-', "horizon")

        # --- Water: vertical reflection streaks under the sun, ripples elsewhere
        for y in range(horizon_row + 1, rows):
            for x in range(cols):
                dx = abs(x - sun_cx)
                if dx < sun_r and (x + y) % 4 < 2:
                    ch = '|' if (x + y) % 8 < 4 else ':'
                    put(y, x, ch, "water_glow")
                elif (x + y * 2) % 7 == 0:
                    put(y, x, '~', "water")

        # --- Palm tree: fixed silhouette, asymmetric, foreground right side
        # Compact hand-authored shape (not procedurally generated) so the
        # canopy stays a clean readable silhouette rather than noisy lines.
        palm_rows = [
            "      __,---.__         ",
            "   _,-'        `-.__    ",
            " ,'        ___      `-, ",
            "/      _,-'   `-._     \\",
            "      '            `    ",
            "                #       ",
            "               ##       ",
            "              ##        ",
            "             ##         ",
            "            ##          ",
            "           ##           ",
            "          ##            ",
        ]
        # Scale the palm down proportionally on small terminals so it
        # doesn't dominate or overflow a narrow window.
        if cols < 60 or rows < 18:
            palm_rows = [
                "  _,--.__      ",
                " '       `-.__ ",
                "          ___`,",
                "       #       ",
                "      ##       ",
                "     ##        ",
                "    ##         ",
            ]

        palm_h = len(palm_rows)
        palm_w = len(palm_rows[0])
        palm_top  = horizon_row - palm_h + max(2, int(palm_h * 0.4))
        palm_left = cols - palm_w - max(2, int(cols * 0.04))

        for ry, line in enumerate(palm_rows):
            gy = palm_top + ry
            for rx, ch in enumerate(line):
                if ch != ' ':
                    put(gy, palm_left + rx, ch, "palm")

        return grid

    def _generate_beach_props(self, rows, cols):
        """Lay out palm trees, umbrella, crab, shells, and gulls once per
        generation, seeded from terminal size so layout is stable across
        redraws but adapts sensibly on resize."""
        g = self.ground_theme
        tallest = g.get("tallest", 9)

        self.beach_palms = []
        for p in g.get("palms", []):
            x = int(cols * p["x_frac"])
            self.beach_palms.append({"x": x, "lean": p["lean"], "h": p.get("h", 5)})

        u = g.get("umbrella")
        self.beach_umbrella = {"x": int(cols * u["x_frac"])} if u else None

        c = g.get("crab")
        self.beach_crab = {"x": int(cols * c["x_frac"])} if c else None

        self.beach_shells = [int(cols * f) for f in g.get("shells", [])]
        rng = random.Random(cols * 7919 + rows * 104729)  # stable per terminal size
        shell_glyphs = ["⋆", "˚", "∘"] if not self.ascii_mode else ["*", ".", "o"]
        self.beach_shell_glyphs = [rng.choice(shell_glyphs) for _ in self.beach_shells]

        self.beach_gulls = []
        for gpos in g.get("gulls", []):
            x = int(cols * gpos["x_frac"])
            y = max(0, rows - tallest - 3 - gpos["row_from_top"])
            self.beach_gulls.append({"x": x, "y": y})

    # ── Sky drawing ────────────────────────────────────────────────────────

    def _draw_sky(self):
        """Draw scattered particles and horizon glow for current sky theme."""
        sky = self.sky_theme

        # Particles
        for (y, x, char, pair) in self.particles:
            self._safe_addstr(y, x, char, curses.color_pair(pair))

        # Beach gulls live in the sky pass so they sit above the horizon glow
        if self.ground_enabled and self.ground_name == "beach":
            self._draw_gulls()

        # Horizon glow — sits just above the ground layer
        rows, cols = self.stdscr.getmaxyx()
        tallest    = self.ground_theme.get("tallest", 10) if self.ground_enabled else 2
        glow_row   = rows - tallest - 2
        if glow_row >= 0:
            glow_char = sky.get("glow_char", "▁")
            for c in range(0, cols - 1):
                char = glow_char if c % 3 == 0 else " "
                self._safe_addstr(
                    glow_row, c, char,
                    curses.color_pair(sky["glow_pair"]) | curses.A_DIM
                )

    def _draw_gulls(self):
        glyph = "v" if self.ascii_mode else "⌃"
        attr = curses.color_pair(self.ground_theme["highlight_pair"]) | curses.A_BOLD
        for gull in getattr(self, "beach_gulls", []):
            self._safe_addstr(gull["y"], gull["x"], glyph, attr)

    # ── Ground drawing ─────────────────────────────────────────────────────

    def _draw_ground(self):
        """Dispatch to the correct ground renderer based on detail_fn."""
        fn_name = self.ground_theme.get("detail_fn")
        dispatch = {
            "city_windows":  self._draw_city,
            "beach_surf":    self._draw_beach,
            "forest_canopy": self._draw_layers,
            "ranch_fence":   self._draw_layers,
            "ocean_waves":   self._draw_layers,
        }
        fn = dispatch.get(fn_name, self._draw_layers)
        fn()

    def _color_attr(self, color_key, bold=False, dim=False):
        """Resolve a color key string to a curses attribute."""
        g = self.ground_theme
        pair_map = {
            "main":      g["color_pair"],
            "accent":    g["accent_pair"],
            "highlight": g["highlight_pair"],
        }
        pair = pair_map.get(color_key, g["color_pair"])
        attr = curses.color_pair(pair)
        if bold:
            attr |= curses.A_BOLD
        if dim:
            attr |= curses.A_DIM
        return attr

    def _safe_addstr(self, y, x, text, attr):
        if y < 0 or x < 0 or not text:
            return
        try:
            self.stdscr.addstr(y, x, text, attr)
        except curses.error:
            pass

    def _glyph(self, char):
        """Return the right glyph for the current render mode."""
        if not self.ascii_mode:
            return char
        return _BEACH_ASCII_FALLBACK.get(char, char)

    def _draw_layers(self):
        """
        Generic layer renderer — used by forest, ranch, ocean, and as a
        safe fallback for beach on very small terminals.
        """
        rows, cols = self.stdscr.getmaxyx()
        g      = self.ground_theme
        layers = g.get("layers", [])

        current_row = rows - 1   # start at the very bottom

        for layer in layers:
            h     = layer["h"]
            chars = layer["chars"]
            attr  = self._color_attr(layer["color"], layer.get("bold", False), layer.get("dim", False))
            chars_len = max(1, len(chars))

            for row_offset in range(h):
                row = current_row - row_offset
                if row < 0:
                    break
                line = (chars * (cols // chars_len + 2))[:max(0, cols - 1)]
                self._safe_addstr(row, 0, line, attr)

            current_row -= h

    # ── Beach renderer ───────────────────────────────────────────────────────

    def _draw_beach(self):
        """
        Beach-specific renderer:
          1. Textured sand bed (stippled, not a single tiled block)
          2. Foam line that gently animates between frames
          3. Two wave bands above the foam
        Then overlays props rooted on the sand: two leaning palm trees,
        a beach umbrella + towel, a crab, and a few scattered shells.
        Gulls are drawn separately in the sky pass.
        """
        rows, cols = self.stdscr.getmaxyx()
        if cols < 20 or rows < 10:
            # Too small to safely place props — fall back to flat bands
            self._draw_layers()
            return

        sand_attr      = self._color_attr("main", bold=True)
        sand_dim_attr  = self._color_attr("main", dim=True)
        foam_attr      = self._color_attr("highlight", bold=True)
        surf_attr      = self._color_attr("accent", bold=True)
        water_attr     = self._color_attr("accent", dim=True)

        bottom = rows - 1

        # --- Sand bed: 2 rows, textured with a small mix of glyphs so it
        #     reads as grainy sand rather than a repeating tiled pattern.
        sand_glyphs = [self._glyph(c) for c in ["▒", "░", "▒", "▓", "░", "·"]]
        rng = random.Random(rows * 31 + cols)  # stable texture per terminal size
        sand_rows = min(2, rows)
        for r in range(sand_rows):
            row = bottom - r
            if row < 0:
                break
            line = "".join(rng.choice(sand_glyphs) for _ in range(max(0, cols - 1)))
            self._safe_addstr(row, 0, line, sand_attr if r == 0 else sand_dim_attr)

        # --- Foam line: alternates glyph offset each frame for a gentle
        #     lapping effect as the screen redraws.
        foam_row = bottom - sand_rows
        if foam_row >= 0:
            offset = self.frame % 2
            pair = [self._glyph("≈"), self._glyph("~")]
            if offset:
                pair.reverse()
            line = "".join((pair[i % 2] + " ") for i in range(cols // 2 + 1))[:max(0, cols - 1)]
            self._safe_addstr(foam_row, 0, line, foam_attr)

        # --- Surf band directly above the foam
        surf_row = foam_row - 1
        if surf_row >= 0:
            line = (self._glyph("≋") + self._glyph("≈")) * (cols // 2 + 1)
            self._safe_addstr(surf_row, 0, line[:max(0, cols - 1)], surf_attr)

        # --- Calmer open-water band above that
        water_row = surf_row - 1
        if water_row >= 0:
            line = (self._glyph("~") + " " + self._glyph("≈") + " ") * (cols // 4 + 1)
            self._safe_addstr(water_row, 0, line[:max(0, cols - 1)], water_attr)

        sand_top_row = bottom - sand_rows + 1  # topmost sand row, where props sit

        self._draw_palms(sand_top_row)
        self._draw_umbrella(sand_top_row)
        self._draw_crab(sand_top_row)
        self._draw_shells(sand_top_row)

    def _draw_palms(self, sand_top_row):
        """Two palm trees, each a leaning trunk topped with a simple
        frond crown — proportions adapted from classic ASCII palm-tree
        sketches (lean trunk of slashes, a compact V-shaped crown)."""
        trunk_attr = self._color_attr("main", dim=True) | curses.A_BOLD
        crown_attr = self._color_attr("accent", bold=True)

        for palm in getattr(self, "beach_palms", []):
            x, lean, h = palm["x"], palm["lean"], palm["h"]
            trunk_glyph = self._glyph("\\") if lean < 0 else self._glyph("/")
            if lean == 0:
                trunk_glyph = self._glyph("|")

            for i in range(h):
                row = sand_top_row - 1 - i
                if row < 0:
                    break
                dx = lean if i >= h // 2 else 0
                self._safe_addstr(row, x + dx, trunk_glyph, trunk_attr)

            crown_row = sand_top_row - 1 - h
            crown_x   = x + (lean if h >= 1 else 0)
            if crown_row >= 0:
                fronds_top = self._glyph("/") + self._glyph("‾") + self._glyph("\\") if not self.ascii_mode else "/^\\"
                self._safe_addstr(crown_row, max(0, crown_x - 1), fronds_top, crown_attr)
            if crown_row + 1 >= 0:
                wide = self._glyph("\\") + self._glyph("_") + self._glyph("/") + " " + self._glyph("\\") + self._glyph("_") + self._glyph("/")
                self._safe_addstr(crown_row + 1, max(0, crown_x - 3), wide, crown_attr)

    def _draw_umbrella(self, sand_top_row):
        """A simple beach umbrella with a pole, plus a folded towel beside it."""
        if not getattr(self, "beach_umbrella", None):
            return
        ux = self.beach_umbrella["x"]
        canopy_attr = self._color_attr("highlight", bold=True)
        pole_attr   = self._color_attr("main", dim=True)
        towel_attr  = self._color_attr("accent")

        canopy_row = sand_top_row - 3
        self._safe_addstr(canopy_row,     ux - 2, " ___ ",  canopy_attr)
        self._safe_addstr(canopy_row + 1, ux - 3, "/___\\", canopy_attr)
        self._safe_addstr(canopy_row + 2, ux,     "|",      pole_attr)
        if sand_top_row - 1 >= 0:
            self._safe_addstr(sand_top_row - 1, ux, "|", pole_attr)

        # Folded towel a couple cells to the side
        self._safe_addstr(sand_top_row, ux + 3, "▭▭▭", towel_attr)

    def _draw_crab(self, sand_top_row):
        """A small crab glyph sitting on the sand — claws, body, claws."""
        if not getattr(self, "beach_crab", None):
            return
        cx = self.beach_crab["x"]
        crab_attr = self._color_attr("highlight")
        crab_glyph = self._glyph("(") + self._glyph("\\") + self._glyph("/") + self._glyph(")") if not self.ascii_mode else "(\\/)"
        self._safe_addstr(sand_top_row, cx, crab_glyph, crab_attr)

    def _draw_shells(self, sand_top_row):
        """A few small shell/starfish marks scattered in the sand."""
        attr = self._color_attr("highlight", dim=True)
        for sx, glyph in zip(getattr(self, "beach_shells", []),
                              getattr(self, "beach_shell_glyphs", [])):
            self._safe_addstr(sand_top_row, sx, glyph, attr)

    def _draw_city(self):
        """
        City-specific renderer — buildings with individually lit windows.
        Kept separate because the logic is per-building, not per-layer.
        """
        rows, cols = self.stdscr.getmaxyx()
        g         = self.ground_theme
        buildings = g.get("buildings", [])
        main_attr = curses.color_pair(g["color_pair"])
        acc_attr  = curses.color_pair(g["accent_pair"])
        hi_attr   = curses.color_pair(g["highlight_pair"])

        col   = 0
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
                    # Ground floor
                    self._safe_addstr(row, col, "▀" * w, main_attr | curses.A_BOLD)

                elif row_offset == h - 1:
                    # Rooftop
                    roof = ("▄" + "─" * (w - 2) + "▄") if w > 2 else "▄" * w
                    self._safe_addstr(row, col, roof, main_attr | curses.A_BOLD)

                else:
                    # Mid floors — walls then windows on top
                    self._safe_addstr(row, col, "█" * w, main_attr)
                    for wc in range(1, w - 1, 2):
                        lit = (row * 7 + (col + wc) * 3) % 5 != 0
                        win_attr = acc_attr if lit else (main_attr | curses.A_DIM)
                        # Every 4th lit window gets bright highlight
                        if lit and (row + col + wc) % 4 == 0:
                            win_attr = hi_attr
                        self._safe_addstr(row, col + wc, b["win"], win_attr)

            col += b["w"] + 1

    # ── Scene drawing (mode="scene") ───────────────────────────────────────

    def _draw_scene(self):
        """Draw the pre-built unified scene grid. Falls back to 'palm'
        pair (or pair id 0) for any pair_key not present in the theme's
        'pairs' map, so a missing curses pair never raises."""
        pairs = self.scene_theme.get("pairs", {})
        grid = getattr(self, "scene_grid", None)
        if not grid:
            return
        rows = len(grid)
        for y in range(rows):
            row = grid[y]
            for x in range(len(row)):
                ch, pair_key = row[x]
                if ch == ' ' or ch is None:
                    continue
                pair_id = pairs.get(pair_key, 0)
                self._safe_addstr(y, x, ch, curses.color_pair(pair_id))

    # ── Public draw ────────────────────────────────────────────────────────

    def draw(self):
        """Draw the active mode. 'layered' draws sky then ground as
        before; 'scene' draws the single unified composition instead.
        frame increments here so beach foam / future scene animation can
        key off it across redraws."""
        if self.mode == "scene":
            self._draw_scene()
        else:
            if self.sky_enabled:
                self._draw_sky()
            if self.ground_enabled:
                self._draw_ground()
        self.frame += 1

    def handle_resize(self):
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        self._generate()
        self.frame = 0