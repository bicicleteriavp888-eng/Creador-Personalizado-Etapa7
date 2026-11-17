"""Componentes reutilizables y adaptables de la interfaz 3.0."""

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLayoutItem,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


def prepare_combo(combo, minimum_contents_length=14):
    """Evita que un ítem largo imponga el ancho mínimo de toda una página.

    Qt dimensiona los QComboBox al texto del ítem más largo. Con etiquetas
    como "Nombre — descripción" eso puede superar el viewport y provocar
    scroll horizontal. AdjustToMinimumContentsLengthWithIcon limita el ancho
    mínimo y el texto se elide en el desplegable.
    """
    combo.setSizeAdjustPolicy(
        QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
    )
    combo.setMinimumContentsLength(int(minimum_contents_length))
    combo.setMinimumWidth(150)
    combo.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
    view = combo.view()
    if view is not None:
        view.setTextElideMode(Qt.TextElideMode.ElideRight)
    return combo


class FlowLayout(QLayout):
    """Layout que distribuye widgets en filas y salta de linea al faltar ancho.

    Se usa para barras de acciones que antes imponian un ancho minimo grande
    (por ejemplo, cuatro botones en una sola fila) y provocaban scroll
    horizontal en ventanas de 1080 px.
    """

    def __init__(self, parent=None, margin=0, h_spacing=10, v_spacing=10):
        super().__init__(parent)
        self._items = []
        self._h_spacing = max(0, int(h_spacing))
        self._v_spacing = max(0, int(v_spacing))
        self.setContentsMargins(margin, margin, margin, margin)

    # -- API requerida por QLayout ------------------------------------------
    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        return size + QSize(
            margins.left() + margins.right(),
            margins.top() + margins.bottom(),
        )

    # -- Distribucion -------------------------------------------------------
    def _do_layout(self, rect, test_only):
        margins = self.contentsMargins()
        effective = rect.adjusted(
            margins.left(), margins.top(), -margins.right(), -margins.bottom()
        )
        x = effective.x()
        y = effective.y()
        line_height = 0

        for item in self._items:
            widget = item.widget()
            if widget is not None and widget.isHidden():
                continue
            hint = item.sizeHint()
            next_x = x + hint.width() + self._h_spacing
            if next_x - self._h_spacing > effective.right() + 1 and line_height > 0:
                x = effective.x()
                y = y + line_height + self._v_spacing
                next_x = x + hint.width() + self._h_spacing
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x = next_x
            line_height = max(line_height, hint.height())

        return y + line_height - rect.y() + margins.bottom()


class PageHeader(QWidget):
    """Encabezado fijo de una pagina del asistente."""

    def __init__(self, title, subtitle="", parent=None):
        super().__init__(parent)
        self.setObjectName("pageHeader")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(4)

        self.title = QLabel(title)
        self.title.setObjectName("pageTitle")
        self.title.setWordWrap(True)
        layout.addWidget(self.title)

        self.subtitle = QLabel(subtitle)
        self.subtitle.setObjectName("pageSubtitle")
        self.subtitle.setWordWrap(True)
        self.subtitle.setVisible(bool(subtitle))
        layout.addWidget(self.subtitle)


class StatusCard(QFrame):
    """Tarjeta de estado con valor, detalle y etiqueta opcional."""

    def __init__(self, title, value="—", detail="", parent=None):
        super().__init__(parent)
        self.setObjectName("statusCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(7)

        header = QHBoxLayout()
        header.setSpacing(8)
        self.title = QLabel(title)
        self.title.setObjectName("cardTitle")
        self.title.setWordWrap(True)
        header.addWidget(self.title, 1)

        self.badge = QLabel("")
        self.badge.setObjectName("cardBadge")
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setVisible(False)
        header.addWidget(self.badge, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        self.value = QLabel(value)
        self.value.setObjectName("cardValue")
        self.value.setWordWrap(True)
        layout.addWidget(self.value)

        self.detail = QLabel(detail)
        self.detail.setObjectName("cardDetail")
        self.detail.setWordWrap(True)
        self.detail.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self.detail)
        layout.addStretch(1)

    def set_content(self, value=None, detail=None, badge=None, state=None):
        if value is not None:
            self.value.setText(value)
        if detail is not None:
            self.detail.setText(detail)
        if badge is not None:
            self.badge.setText(badge)
            self.badge.setVisible(bool(badge))
        if state is not None:
            self.badge.setProperty("state", state)
            self.badge.style().unpolish(self.badge)
            self.badge.style().polish(self.badge)


class SectionCard(QFrame):
    """Panel con titulo, subtitulo y un cuerpo donde agregar widgets."""

    def __init__(self, title, subtitle="", parent=None):
        super().__init__(parent)
        self.setObjectName("sectionCard")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(8)

        self.title = QLabel(title)
        self.title.setObjectName("sectionTitle")
        self.title.setWordWrap(True)
        outer.addWidget(self.title)

        self.subtitle = QLabel(subtitle)
        self.subtitle.setObjectName("sectionSubtitle")
        self.subtitle.setWordWrap(True)
        self.subtitle.setVisible(bool(subtitle))
        outer.addWidget(self.subtitle)

        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 2, 0, 0)
        self.body.setSpacing(10)
        outer.addLayout(self.body)

    def add_widget(self, widget):
        self.body.addWidget(widget)
        return widget

    def add_layout(self, layout):
        self.body.addLayout(layout)
        return layout


class EmptyState(QFrame):
    """Estado vacio consistente: explica que falta y como continuar."""

    def __init__(self, title, detail="", parent=None):
        super().__init__(parent)
        self.setObjectName("emptyState")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(6)
        self.title = QLabel(title)
        self.title.setObjectName("emptyTitle")
        self.title.setWordWrap(True)
        layout.addWidget(self.title)
        self.detail = QLabel(detail)
        self.detail.setObjectName("emptyDetail")
        self.detail.setWordWrap(True)
        self.detail.setVisible(bool(detail))
        layout.addWidget(self.detail)


class HelpPanel(QFrame):
    """Ayuda contextual plegable, compartida por todas las paginas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("helpPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(5)

        self.title = QLabel("Ayuda contextual")
        self.title.setObjectName("helpTitle")
        layout.addWidget(self.title)

        self.body = QTextBrowser()
        self.body.setObjectName("helpBody")
        self.body.setOpenExternalLinks(False)
        self.body.setMinimumHeight(96)
        self.body.setMaximumHeight(150)
        layout.addWidget(self.body)

    def set_content(self, title, html):
        self.title.setText(title)
        self.body.setHtml(html)
        self.body.verticalScrollBar().setValue(0)


class Card(QFrame):
    """Contenedor simple para agrupar controles con el estilo de tarjeta."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusCard")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(16, 14, 16, 14)
        self.body.setSpacing(10)


def configure_image_preview(label, *, minimum=(220, 130), maximum=(480, 260)):
    """Configura una vista previa que se adapta al ancho disponible.

    Evita que las imágenes de muestra impongan un ancho fijo a la página;
    ImageField conserva el escalado proporcional de la imagen.
    """
    label.setMinimumSize(*minimum)
    label.setMaximumSize(*maximum)
    label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    label.setScaledContents(False)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return label
