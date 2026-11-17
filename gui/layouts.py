"""Helpers de composicion para paginas consistentes y desplazables."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QGroupBox,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from gui.components import PageHeader


def add_page(gui, key, page, title, subtitle, help_text, *, step=None, content_width=1180):
    """Registra una pagina con encabezado fijo y contenido desplazable."""
    page.setObjectName("pageContent")
    page.setMinimumWidth(0)
    page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    if content_width:
        page.setMaximumWidth(content_width)

    layout = page.layout()
    if layout is not None:
        layout.setContentsMargins(24, 22, 24, 26)
        layout.setSpacing(18)
        _polish_nested_layouts(layout)

    container = QWidget()
    container_layout = QVBoxLayout(container)
    container_layout.setContentsMargins(0, 0, 0, 0)
    container_layout.setSpacing(14)
    container_layout.addWidget(PageHeader(title, subtitle))

    scroll = QScrollArea()
    scroll.setObjectName("pageScrollArea")
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
    scroll.setWidget(page)
    container_layout.addWidget(scroll, 1)

    gui.register_page(key, container, title, subtitle, help_text, step)
    return container


def _polish_nested_layouts(layout):
    """Uniforma el ritmo visual sin alterar la estructura funcional."""
    if isinstance(layout, QFormLayout):
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(14)
    else:
        layout.setSpacing(max(layout.spacing(), 12))

    for index in range(layout.count()):
        item = layout.itemAt(index)
        if item is None:
            continue
        child = item.layout()
        if child is not None:
            _polish_nested_layouts(child)
            continue
        widget = item.widget()
        if isinstance(widget, QGroupBox) and widget.layout() is not None:
            group_layout = widget.layout()
            group_layout.setContentsMargins(14, 14, 14, 12)
            group_layout.setSpacing(max(group_layout.spacing(), 12))
            _polish_nested_layouts(group_layout)
