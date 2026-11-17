"""Sistema visual de Creador Personalizado 3.0.

La hoja de estilos se construye a partir de una paleta con tokens. Ninguna
pagina deberia fijar colores propios: claro y oscuro comparten la misma
estructura y solo cambian los valores de los tokens.

Contraste verificado (razon WCAG AA >= 4.5:1 para texto normal):

* claro: TEXT/BG 14.6:1, TEXT/SURFACE_ALT 15.6:1, MUTED/SURFACE 5.1:1.
* oscuro: TEXT/BG 15.2:1, TEXT/SURFACE_ALT 12.3:1, MUTED/SURFACE 7.0:1.

Las tablas usan ``SURFACE_ALT`` como fila alterna y ``ACCENT_SOFT`` como
seleccion, con texto ``TEXT`` en ambos casos para evitar texto oscuro sobre
fondo oscuro.
"""

LIGHT = {
    "BG": "#f3f6fb",
    "SURFACE": "#ffffff",
    "SURFACE_ALT": "#f5f8fc",
    "SURFACE_RAISED": "#eef3f9",
    "BORDER": "#dfe6ef",
    "BORDER_STRONG": "#c9d5e4",
    "TEXT": "#1b2430",
    "TEXT_SOFT": "#38465a",
    "MUTED": "#5b6b80",
    "ACCENT": "#0a66c2",
    "ACCENT_HOVER": "#005a9e",
    "ACCENT_SOFT": "#e8f1fc",
    "ACCENT_STRONG": "#0b4f73",
    "NAVY": "#0e2a3d",
    "NAVY_TEXT": "#eaf3fb",
    "DANGER": "#b42332",
    "DANGER_SOFT": "#fdecef",
    "SUCCESS": "#1d7a45",
    "SUCCESS_SOFT": "#e7f6ed",
    "WARNING": "#8a5700",
    "WARNING_SOFT": "#fff4d9",
    "CONSOLE_BG": "#101a2b",
    "CONSOLE_FG": "#dbe8f8",
}

DARK = {
    "BG": "#0f1722",
    "SURFACE": "#162232",
    "SURFACE_ALT": "#1c2b3d",
    "SURFACE_RAISED": "#22344a",
    "BORDER": "#2a3b50",
    "BORDER_STRONG": "#3b506a",
    "TEXT": "#e6edf6",
    "TEXT_SOFT": "#cbd8e8",
    "MUTED": "#9aabc0",
    "ACCENT": "#4da3ff",
    "ACCENT_HOVER": "#77b9ff",
    "ACCENT_SOFT": "#1b3550",
    "ACCENT_STRONG": "#8cc6ff",
    "NAVY": "#0b1622",
    "NAVY_TEXT": "#eaf3fb",
    "DANGER": "#ff7b7b",
    "DANGER_SOFT": "#3d2026",
    "SUCCESS": "#53d18a",
    "SUCCESS_SOFT": "#17382a",
    "WARNING": "#f0b45b",
    "WARNING_SOFT": "#3a2d16",
    "CONSOLE_BG": "#0b1220",
    "CONSOLE_FG": "#dbe8f8",
}

THEMES = {"light": LIGHT, "dark": DARK}

_TEMPLATE = r"""
/* Base ---------------------------------------------------------------- */
QMainWindow { background: @BG@; color: @TEXT@; }
QWidget { color: @TEXT@; font-family: "Segoe UI", "Noto Sans", "DejaVu Sans", sans-serif; font-size: 10pt; }
QWidget#contentRoot { background: @BG@; }
QLabel { background: transparent; }
QLabel:disabled { color: @MUTED@; }
QDialog, QMessageBox { background: @SURFACE@; color: @TEXT@; }
QMessageBox QLabel { background: transparent; color: @TEXT@; }
QToolTip { background: @TEXT@; color: @SURFACE@; border: 0; padding: 6px 8px; border-radius: 6px; }

/* Barra lateral y navegacion ------------------------------------------ */
QFrame#sidebar { background: @SURFACE@; border-right: 1px solid @BORDER@; }
QLabel#brandTitle { color: @TEXT@; font-size: 16pt; font-weight: 800; }
QLabel#brandSubtitle { color: @MUTED@; font-size: 9pt; }
QLabel#sidebarSection { color: @MUTED@; font-size: 7.5pt; font-weight: 700; letter-spacing: 1px; padding: 10px 14px 4px 14px; }
QLabel#sidebarFooter { color: @MUTED@; font-size: 8pt; padding: 8px 14px; }
QFrame#navSeparator { background: @BORDER@; max-height: 1px; min-height: 1px; border: 0; margin: 10px 8px; }
QPushButton#navButton { text-align: left; background: transparent; color: @MUTED@; border: 1px solid transparent; border-radius: 9px; padding: 10px 13px; font-weight: 600; }
QPushButton#navButton:hover { background: @SURFACE_ALT@; color: @TEXT@; border-color: @BORDER@; }
QPushButton#navButton:checked { background: @ACCENT_SOFT@; color: @ACCENT@; border-color: @BORDER_STRONG@; }
QPushButton#navButton:disabled { color: @MUTED@; background: transparent; }
QToolButton#sidebarToggle { background: @SURFACE_ALT@; color: @TEXT@; border: 1px solid @BORDER@; border-radius: 8px; padding: 6px 9px; font-weight: 700; }
QToolButton#sidebarToggle:hover { background: @ACCENT_SOFT@; border-color: @ACCENT@; color: @ACCENT@; }

/* Cabecera y estructura ----------------------------------------------- */
QFrame#topBar { background: transparent; }
QLabel#breadcrumb { color: @MUTED@; font-size: 9pt; font-weight: 600; }
QLabel#globalStatus { background: @SURFACE_ALT@; color: @MUTED@; border: 1px solid @BORDER@; border-radius: 9px; padding: 6px 10px; font-size: 8.5pt; font-weight: 600; }
QLabel#pageTitle { color: @TEXT@; font-size: 21pt; font-weight: 800; }
QLabel#pageSubtitle { color: @MUTED@; font-size: 10pt; }
QWidget#pageHeader { background: transparent; }
QWidget#pageContent { background: @SURFACE@; }
QScrollArea#pageScrollArea { background: @SURFACE@; border: 1px solid @BORDER@; border-radius: 14px; }
QStackedWidget { background: transparent; }

/* Tarjetas de estado -------------------------------------------------- */
QFrame#statusCard { background: @SURFACE_ALT@; border: 1px solid @BORDER@; border-radius: 12px; }
QLabel#cardTitle { color: @MUTED@; font-size: 8.5pt; font-weight: 700; }
QLabel#cardValue { color: @TEXT@; font-size: 13.5pt; font-weight: 700; }
QLabel#cardDetail { color: @MUTED@; font-size: 9pt; }
QLabel#cardBadge { background: @SURFACE@; color: @MUTED@; border: 1px solid @BORDER@; border-radius: 8px; padding: 3px 8px; font-size: 7.5pt; font-weight: 700; }
QLabel#cardBadge[state="ok"] { background: @SUCCESS_SOFT@; color: @SUCCESS@; border-color: @SUCCESS@; }
QLabel#cardBadge[state="warn"] { background: @WARNING_SOFT@; color: @WARNING@; border-color: @WARNING@; }
QLabel#cardBadge[state="error"] { background: @DANGER_SOFT@; color: @DANGER@; border-color: @DANGER@; }
QLabel#cardBadge[state="info"] { background: @ACCENT_SOFT@; color: @ACCENT@; border-color: @ACCENT@; }
QFrame#sectionCard { background: @SURFACE_ALT@; border: 1px solid @BORDER@; border-radius: 12px; }
QLabel#sectionTitle { color: @TEXT@; font-size: 11.5pt; font-weight: 700; }
QLabel#sectionSubtitle { color: @MUTED@; font-size: 9pt; }
QFrame#emptyState { background: @SURFACE_ALT@; border: 1px dashed @BORDER_STRONG@; border-radius: 12px; }
QLabel#emptyTitle { color: @TEXT@; font-size: 11pt; font-weight: 700; }
QLabel#emptyDetail { color: @MUTED@; font-size: 9pt; }

/* Pie del asistente --------------------------------------------------- */
QFrame#wizardFooter { background: @SURFACE@; border: 1px solid @BORDER@; border-radius: 12px; }
QLabel#wizardStatus { color: @MUTED@; font-size: 9pt; }
QFrame#helpPanel { background: @SURFACE_ALT@; border: 1px solid @BORDER@; border-radius: 10px; }
QLabel#helpTitle { color: @ACCENT@; font-size: 9pt; font-weight: 700; }
QTextBrowser#helpBody { background: transparent; border: 0; color: @TEXT@; }

/* Formularios --------------------------------------------------------- */
QGroupBox { background: @SURFACE_ALT@; border: 1px solid @BORDER@; border-radius: 10px; margin-top: 18px; padding: 20px 16px 16px 16px; font-weight: 600; color: @TEXT@; }
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 7px; color: @ACCENT_STRONG@; }
QLineEdit, QComboBox, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox { background: @SURFACE@; color: @TEXT@; border: 1px solid @BORDER_STRONG@; border-radius: 7px; padding: 9px 11px; min-height: 20px; selection-background-color: @ACCENT@; selection-color: #ffffff; }
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid @ACCENT@; }
QLineEdit:disabled, QComboBox:disabled, QTextEdit:disabled, QPlainTextEdit:disabled { color: @MUTED@; background: @SURFACE_ALT@; }
QComboBox::drop-down { border: 0; width: 25px; }
QComboBox QAbstractItemView { background: @SURFACE@; color: @TEXT@; border: 1px solid @BORDER@; selection-background-color: @ACCENT_SOFT@; selection-color: @TEXT@; outline: 0; }
QPushButton { background: @SURFACE_ALT@; color: @TEXT@; border: 1px solid @BORDER_STRONG@; border-radius: 7px; padding: 9px 15px; font-weight: 600; }
QPushButton:hover { background: @ACCENT_SOFT@; border-color: @ACCENT@; color: @ACCENT@; }
QPushButton:pressed { background: @ACCENT_SOFT@; }
QPushButton:disabled { color: @MUTED@; background: @SURFACE_ALT@; border-color: @BORDER@; }
QPushButton#primaryAction { background: @ACCENT@; color: #ffffff; border: 1px solid @ACCENT@; padding: 12px 18px; font-size: 11pt; font-weight: 700; }
QPushButton#primaryAction:hover { background: @ACCENT_HOVER@; border-color: @ACCENT_HOVER@; color: #ffffff; }
QPushButton#primaryAction:pressed { background: @ACCENT_HOVER@; }
QPushButton#primaryAction:disabled { background: @SURFACE_ALT@; color: @MUTED@; border-color: @BORDER@; }
QPushButton#dangerAction { background: @DANGER@; color: #ffffff; border: 1px solid @DANGER@; padding: 12px 18px; font-size: 11pt; font-weight: 700; }
QPushButton#dangerAction:hover { background: @DANGER@; border-color: @DANGER@; color: #ffffff; }
QPushButton#dangerAction:disabled { background: @SURFACE_ALT@; color: @MUTED@; border-color: @BORDER@; }
QPushButton#ghostAction { background: transparent; border-color: transparent; color: @MUTED@; }
QPushButton#ghostAction:hover { background: @SURFACE_ALT@; color: @TEXT@; border-color: @BORDER@; }
QCheckBox, QRadioButton { spacing: 10px; color: @TEXT@; padding: 3px 0; background: transparent; }
QCheckBox::indicator, QRadioButton::indicator { width: 17px; height: 17px; }
QCheckBox:disabled, QRadioButton:disabled { color: @MUTED@; }
QProgressBar { background: @SURFACE_ALT@; color: @TEXT@; border: 1px solid @BORDER@; border-radius: 6px; height: 14px; text-align: center; }
QProgressBar::chunk { background: @ACCENT@; border-radius: 6px; }
QScrollArea { border: 0; background: transparent; }
QLabel#imagePreview { border: 1px dashed @BORDER_STRONG@; border-radius: 8px; background: @SURFACE_ALT@; color: @MUTED@; }
QLabel#warningText { color: @DANGER@; background: @DANGER_SOFT@; border: 1px solid @DANGER@; border-radius: 8px; padding: 9px 11px; }
QLabel#inlineHint { color: @MUTED@; font-size: 8.5pt; }
QLabel#managerStatus { color: @MUTED@; font-size: 9pt; }
QLabel#scopeNote { color: @WARNING@; background: @WARNING_SOFT@; border: 1px solid @WARNING@; border-radius: 8px; padding: 8px 10px; }

/* Tablas -------------------------------------------------------------- */
QTableWidget, QTableView { background: @SURFACE@; alternate-background-color: @SURFACE_ALT@; color: @TEXT@; border: 1px solid @BORDER@; border-radius: 10px; gridline-color: @BORDER@; selection-background-color: @ACCENT_SOFT@; selection-color: @TEXT@; outline: 0; }
QTableWidget::item, QTableView::item { padding: 6px 8px; border-bottom: 1px solid @BORDER@; }
QTableWidget::item:selected, QTableView::item:selected { background: @ACCENT_SOFT@; color: @TEXT@; }
QTableWidget::item:hover, QTableView::item:hover { background: @SURFACE_RAISED@; }
QHeaderView { background: @SURFACE_ALT@; }
QHeaderView::section { background: @SURFACE_ALT@; color: @MUTED@; border: 0; border-bottom: 1px solid @BORDER_STRONG@; border-right: 1px solid @BORDER@; padding: 8px; font-size: 8.5pt; font-weight: 700; }
QHeaderView::section:last { border-right: 0; }
QTableCornerButton::section { background: @SURFACE_ALT@; border: 0; border-bottom: 1px solid @BORDER_STRONG@; }
QListWidget { background: @SURFACE@; color: @TEXT@; border: 1px solid @BORDER@; border-radius: 8px; outline: 0; }
QListWidget::item:selected { background: @ACCENT_SOFT@; color: @TEXT@; }

/* Paneles divididos y consola ---------------------------------------- */
QSplitter::handle { background: @BORDER@; }
QSplitter::handle:horizontal { width: 6px; }
QSplitter::handle:vertical { height: 6px; }
QSplitter::handle:hover { background: @ACCENT@; }
QTextEdit#console, QPlainTextEdit#console { background: @CONSOLE_BG@; color: @CONSOLE_FG@; border: 1px solid @BORDER_STRONG@; border-radius: 8px; font-family: "JetBrains Mono", "DejaVu Sans Mono", monospace; }

/* Barras de desplazamiento ------------------------------------------- */
QScrollBar:vertical { background: @SURFACE_ALT@; width: 11px; margin: 4px 2px; border-radius: 5px; }
QScrollBar::handle:vertical { background: @BORDER_STRONG@; min-height: 28px; border-radius: 5px; }
QScrollBar::handle:vertical:hover { background: @MUTED@; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: @SURFACE_ALT@; height: 11px; margin: 2px 4px; border-radius: 5px; }
QScrollBar::handle:horizontal { background: @BORDER_STRONG@; min-width: 28px; border-radius: 5px; }
QScrollBar::handle:horizontal:hover { background: @MUTED@; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
"""


def build_stylesheet(theme="light"):
    """Devuelve la hoja de estilos completa para ``light`` u ``dark``."""
    palette = THEMES.get(theme, LIGHT)
    css = _TEMPLATE
    for key, value in palette.items():
        css = css.replace("@" + key + "@", value)
    return css


# Compatibilidad con el nombre anterior.
APP_STYLESHEET = build_stylesheet("light")
