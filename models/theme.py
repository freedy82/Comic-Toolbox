from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets


def apply_color_scheme(app, name):
    # Default and Green stay light even when Windows switches to dark mode.
    scheme = QtCore.Qt.ColorScheme.Dark if (name or "").lower() == "dark" else QtCore.Qt.ColorScheme.Light
    app.styleHints().setColorScheme(scheme)


def _windows_control_style(app):
    if not hasattr(app, "_windows_control_style"):
        # This is the native Windows style used before the Qt6 migration.
        # Qt6's Windows 11 style draws progress bars as thin lines and gives
        # menu items more vertical padding.
        style = QtWidgets.QStyleFactory.create("windowsvista")
        if style is not None:
            style.setParent(app)
        app._windows_control_style = style
    return app._windows_control_style


def _native_menu_layout(app):
    style = _windows_control_style(app) or app.style()
    # Capture widget-specific Windows metrics before application QSS changes
    # them. Calculating without a widget can use the fallback style instead.
    window = QtWidgets.QMainWindow()
    central = QtWidgets.QWidget(window)
    window.setCentralWidget(central)
    layout = QtWidgets.QVBoxLayout(central)
    app._native_layout_margins = layout.contentsMargins()
    app._native_layout_spacing = layout.spacing()
    bar = QtWidgets.QMenuBar(window)
    bar.setStyle(style)
    bar.setNativeMenuBar(False)
    bar.setFont(app.font("QMenuBar"))
    window.setMenuBar(bar)
    action = bar.addAction("Menu")
    bar.ensurePolished()
    bar_size = bar.sizeHint()
    bar_item = bar.actionGeometry(action)

    menu = QtWidgets.QMenu(window)
    menu.setStyle(style)
    menu.setFont(bar.font())
    option = QtWidgets.QStyleOptionMenuItem()
    option.initFrom(menu)
    option.font = bar.font()
    option.fontMetrics = QtGui.QFontMetrics(option.font)
    option.text = "Menu"
    option.menuItemType = QtWidgets.QStyleOptionMenuItem.MenuItemType.Normal
    icon_size = style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_SmallIconSize, option, menu)
    option.maxIconWidth = icon_size
    text_width = option.fontMetrics.horizontalAdvance(option.text)
    text_height = option.fontMetrics.height()
    item_size = style.sizeFromContents(
        QtWidgets.QStyle.ContentsType.CT_MenuItem, option, QtCore.QSize(text_width, max(text_height, icon_size)), menu
    )
    bar_padding = max(0, bar_item.width() - text_width)
    bar_left = bar_padding // 2
    bar_right = bar_padding - bar_left
    bar_top = max(0, bar_item.top())
    bar_bottom = max(0, bar_size.height() - bar_item.bottom() - 1)
    bar_side = max(0, bar_item.left())
    bar_spacing = style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_MenuBarItemSpacing, None, bar)
    window.deleteLater()

    # Use logical pixels; Qt applies the screen's DPI scale to these metrics.
    return f"""
        QMenu {{
            border: 1px solid palette(mid);
            padding: 2px;
        }}
        QMenu::item {{
            min-height: {item_size.height()}px;
            padding: 0px 20px 0px 8px;
            border: 0px;
        }}
        QMenu::icon {{
            subcontrol-origin: padding;
            subcontrol-position: center left;
            left: 4px;
        }}
        QMenuBar {{
            border: 0px;
            min-height: {bar_item.height()}px;
            padding: {bar_top}px {bar_side}px {bar_bottom}px {bar_side}px;
            spacing: {bar_spacing}px;
        }}
        QMenuBar::item {{
            min-height: {bar_item.height()}px;
            padding: 0px {bar_right}px 0px {bar_left}px;
            border: 0px;
        }}
    """


def apply_theme(app, name):
    # Capture Default metrics once, before any theme replaces the native style.
    if not hasattr(app, "_menu_layout_style"):
        apply_color_scheme(app, "default")
        app._menu_layout_style = _native_menu_layout(app)
    apply_color_scheme(app, name)
    theme_style = ""
    if name:
        theme_path = Path(__file__).resolve().parent.parent / "themes" / f"{name}.qss"
        theme_style = theme_path.read_text(encoding="utf-8")
    # Keep Default menus native, including Windows hover colors and borders.
    if name not in ("", "default"):
        theme_style = app._menu_layout_style + "\n" + theme_style
    app.setStyleSheet(theme_style)
    # Existing rich text retains the link colors from the palette it was
    # parsed with. Refresh it after Qt applies the new color scheme, using
    # the same native link color as a newly opened About Qt dialog.
    QtCore.QTimer.singleShot(0, lambda: _refresh_link_colors(app))


def _refresh_link_colors(app):
    link_color = app.palette("QMessageBox").color(QtGui.QPalette.ColorRole.Link)
    for widget in app.allWidgets():
        if isinstance(widget, QtWidgets.QLabel):
            text = widget.text()
            if widget.textFormat() != QtCore.Qt.TextFormat.PlainText and "<a " in text.lower():
                if text == widget.property("_theme_link_rendered"):
                    text = widget.property("_theme_link_original")
                rendered = f"<style>a {{color: {link_color.name()};}}</style>{text}"
                widget.setProperty("_theme_link_original", text)
                widget.setProperty("_theme_link_rendered", rendered)
                widget.setText(rendered)
        elif isinstance(widget, QtWidgets.QTextBrowser):
            # HTML exported by QTextDocument stores explicit colors. Update
            # anchor fragments directly, preserving the content and scroll.
            document = widget.document()
            anchors = []
            block = document.begin()
            while block.isValid():
                iterator = block.begin()
                while not iterator.atEnd():
                    fragment = iterator.fragment()
                    if fragment.isValid() and fragment.charFormat().anchorHref():
                        anchors.append((fragment.position(), fragment.length()))
                    iterator += 1
                block = block.next()
            link_format = QtGui.QTextCharFormat()
            link_format.setForeground(link_color)
            cursor = QtGui.QTextCursor(document)
            for position, length in anchors:
                cursor.setPosition(position)
                cursor.setPosition(position + length, QtGui.QTextCursor.MoveMode.KeepAnchor)
                cursor.mergeCharFormat(link_format)


def apply_native_layout(app, ui):
    if not hasattr(app, "_menu_layout_style"):
        app._menu_layout_style = _native_menu_layout(app)
    # These generated main-window layouts all use implicit style defaults.
    # Pin them once so stylesheet changes cannot shrink the surrounding gaps.
    # Nested layouts retain their native zero margins; widget layouts use the
    # captured Windows margins. Internal Qt layouts are left to their widgets.
    control_style = _windows_control_style(app)
    for item in vars(ui).values():
        if isinstance(item, QtWidgets.QLayout):
            margins = app._native_layout_margins if isinstance(item.parent(), QtWidgets.QWidget) else QtCore.QMargins()
            item.setContentsMargins(margins)
            item.setSpacing(app._native_layout_spacing)
        elif control_style is not None and isinstance(
            item, (QtWidgets.QProgressBar, QtWidgets.QMenuBar, QtWidgets.QMenu)
        ):
            item.setStyle(control_style)


def apply_native_progress_bar(app, progress_bar):
    style = _windows_control_style(app)
    if style is not None:
        progress_bar.setStyle(style)


def apply_native_toolbar(app, toolbar):
    style = _windows_control_style(app)
    if style is not None:
        toolbar.setStyle(style)
        # QAction buttons are created internally by QToolBar; style those as
        # well as the reader's explicitly added tool buttons.
        for button in toolbar.findChildren(QtWidgets.QToolButton):
            button.setStyle(style)


def empty_menu_icon(app):
    size = app.style().pixelMetric(QtWidgets.QStyle.PixelMetric.PM_SmallIconSize)
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.GlobalColor.transparent)
    return QtGui.QIcon(pixmap)
