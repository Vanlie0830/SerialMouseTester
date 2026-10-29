"""
Centralized Theme Module (QSS Variables)

Inspired by VVT Expert's CSS variable pattern.
All colors, fonts, and styles are defined HERE ONLY.
Change the theme by modifying this file alone.
"""

# ═══════════════════════════════════════════
# Catppuccin Mocha Palette
# ═══════════════════════════════════════════
class Palette:
    """Catppuccin Mocha color palette - single source of truth."""
    BASE       = "#1e1e2e"
    MANTLE     = "#181825"
    CRUST      = "#11111b"
    SURFACE0   = "#313244"
    SURFACE1   = "#45475a"
    SURFACE2   = "#585b70"
    OVERLAY0   = "#6c7086"
    OVERLAY1   = "#7f849c"
    SUBTEXT0   = "#a6adc8"
    SUBTEXT1   = "#bac2de"
    TEXT       = "#cdd6f4"
    LAVENDER   = "#b4befe"
    BLUE       = "#89b4fa"
    SAPPHIRE   = "#74c7ec"
    SKY        = "#89dceb"
    TEAL       = "#94e2d5"
    GREEN      = "#a6e3a1"
    YELLOW     = "#f9e2af"
    PEACH      = "#fab387"
    MAROON     = "#eba0ac"
    RED        = "#f38ba8"
    MAUVE      = "#cba6f7"

    # Semantic aliases
    BG         = CRUST
    BG_CARD    = BASE
    BG_INPUT   = SURFACE0
    BORDER     = SURFACE1
    BORDER_HOVER = BLUE
    TEXT_PRIMARY = TEXT
    TEXT_SECONDARY = SUBTEXT0
    TEXT_MUTED = OVERLAY0
    ACCENT     = BLUE
    ACCENT_HOVER = SAPPHIRE
    SUCCESS    = GREEN
    WARNING    = PEACH
    DANGER     = RED
    INFO       = SAPPHIRE


class Fonts:
    """Font definitions."""
    UI = "Segoe UI"
    MONO = "Consolas"
    UI_SIZE = 10
    SMALL_SIZE = 9
    LARGE_SIZE = 14
    HEADING_SIZE = 12


# ═══════════════════════════════════════════
# QSS Stylesheets (use Palette values only)
# ═══════════════════════════════════════════

MAIN_WINDOW_QSS = f"""
QMainWindow {{
    background-color: {Palette.CRUST};
}}
QMenuBar {{
    background-color: {Palette.BASE};
    color: {Palette.TEXT};
    border-bottom: 1px solid {Palette.SURFACE0};
    padding: 2px;
}}
QMenuBar::item:selected {{
    background-color: {Palette.SURFACE0};
    border-radius: 4px;
}}
QMenu {{
    background-color: {Palette.BASE};
    color: {Palette.TEXT};
    border: 1px solid {Palette.SURFACE1};
    border-radius: 6px;
    padding: 4px;
}}
QMenu::item:selected {{
    background-color: {Palette.SURFACE1};
    border-radius: 4px;
}}
QToolBar {{
    background-color: {Palette.BASE};
    border-bottom: 1px solid {Palette.SURFACE0};
    padding: 4px;
    spacing: 4px;
}}
QStatusBar {{
    background-color: {Palette.MANTLE};
    color: {Palette.SUBTEXT0};
    border-top: 1px solid {Palette.SURFACE0};
    font-size: 11px;
}}
QSplitter::handle {{
    background-color: {Palette.SURFACE0};
    width: 2px;
}}
QSplitter::handle:hover {{
    background-color: {Palette.BLUE};
}}
"""

SIDEBAR_QSS = f"""
QWidget#Sidebar {{
    background-color: {Palette.MANTLE};
    border-right: 1px solid {Palette.SURFACE0};
    min-width: 200px;
    max-width: 200px;
}}
QPushButton[nav="true"] {{
    background-color: transparent;
    color: {Palette.SUBTEXT0};
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 13px;
    font-weight: bold;
    text-align: left;
}}
QPushButton[nav="true"]:hover {{
    background-color: {Palette.SURFACE0};
    color: {Palette.TEXT};
}}
QPushButton[nav="true"][active="true"] {{
    background-color: {Palette.BLUE};
    color: {Palette.CRUST};
}}
"""

CARD_QSS = f"""
QFrame[card="true"] {{
    background-color: {Palette.BASE};
    border: 1px solid {Palette.SURFACE1};
    border-radius: 10px;
    padding: 16px;
}}
QLabel[card-title="true"] {{
    color: {Palette.SUBTEXT0};
    font-size: 11px;
    font-weight: bold;
}}
QLabel[card-value="true"] {{
    color: {Palette.TEXT};
    font-size: 24px;
    font-weight: bold;
}}
QLabel[card-sub="true"] {{
    color: {Palette.OVERLAY0};
    font-size: 10px;
}}
"""

BUTTON_QSS = f"""
QPushButton {{
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: bold;
}}
QPushButton[variant="primary"] {{
    background-color: {Palette.GREEN};
    color: {Palette.CRUST};
}}
QPushButton[variant="primary"]:hover {{
    background-color: {Palette.TEAL};
}}
QPushButton[variant="danger"] {{
    background-color: {Palette.RED};
    color: {Palette.CRUST};
}}
QPushButton[variant="danger"]:hover {{
    background-color: {Palette.MAROON};
}}
QPushButton[variant="secondary"] {{
    background-color: {Palette.SURFACE1};
    color: {Palette.TEXT};
}}
QPushButton[variant="secondary"]:hover {{
    background-color: {Palette.SURFACE2};
}}
QPushButton:disabled {{
    background-color: {Palette.SURFACE1};
    color: {Palette.OVERLAY0};
}}
"""

INPUT_QSS = f"""
QComboBox, QSpinBox, QLineEdit {{
    background-color: {Palette.SURFACE0};
    color: {Palette.TEXT};
    border: 1px solid {Palette.SURFACE1};
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 12px;
}}
QComboBox:hover, QSpinBox:hover, QLineEdit:hover {{
    border-color: {Palette.BLUE};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background-color: {Palette.SURFACE0};
    color: {Palette.TEXT};
    selection-background-color: {Palette.SURFACE2};
}}
"""

TABLE_QSS = f"""
QTableWidget {{
    background-color: {Palette.BASE};
    color: {Palette.TEXT};
    alternate-background-color: {Palette.MANTLE};
    border: 1px solid {Palette.SURFACE1};
    border-radius: 6px;
    gridline-color: {Palette.SURFACE0};
}}
QTableWidget::item {{
    padding: 4px;
}}
QHeaderView::section {{
    background-color: {Palette.SURFACE0};
    color: {Palette.TEXT};
    border: 1px solid {Palette.SURFACE1};
    padding: 6px;
    font-weight: bold;
}}
"""

# Combined full application stylesheet
FULL_QSS = "\n".join([
    MAIN_WINDOW_QSS,
    SIDEBAR_QSS,
    CARD_QSS,
    BUTTON_QSS,
    INPUT_QSS,
    TABLE_QSS,
])


def get_palette() -> Palette:
    """Get the color palette (for programmatic use)."""
    return Palette()
