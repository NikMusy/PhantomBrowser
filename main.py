# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════╗
║   PHANTOM BROWSER v3  ·  убийца Chrome и Comet на PyQt6                     ║
║   ----------------------------------------------------------------------   ║
║   Каркас «как в Chrome»: вкладки ВНУТРИ заголовка окна (Win32 custom        ║
║   frame через WM_NCCALCSIZE / WM_NCHITTEST). Сохранены НАТИВНЫЕ Aero Snap,  ║
║   изменение размера, тень, анимации сворачивания/разворачивания. Кнопки     ║
║   окна нарисованы шрифтом Segoe Fluent Icons — выглядят как системные.      ║
║                                                                            ║
║   Поиск:  своя поисковая система «Phantom Search» (приватный бэкенд).       ║
║   Chrome: вкладки, умный Omnibox, загрузки, поиск (Ctrl+F), зум, закладки,  ║
║           история, восстановление сессии, меню, «браузер по умолчанию».     ║
║   Comet:  ✨ боковая AI-панель (Claude API) — резюме и чат по странице.     ║
║   Privacy:GHOST MODE — Tor SOCKS5 + спуфинг UA + Off-The-Record профиль.    ║
║   Прочее: 🚀 Antigravity, блокировщик трекеров, готов к сборке в .exe.       ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import sys
import re
import os
import json
import time
import socket
import ctypes
import urllib.request
import urllib.error
import urllib.parse
from html import escape as esc

from PyQt6.QtCore import (
    Qt, QUrl, QPoint, QRectF, QEvent, QTimer, QThread, QObject,
    QPropertyAnimation, QVariantAnimation, QEasingCurve, pyqtSignal,
)
from PyQt6.QtGui import (
    QShortcut, QKeySequence, QAction,
    QPainter, QColor, QLinearGradient, QFont, QPen, QBrush,
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QStackedWidget, QTabBar, QProgressBar,
    QSizeGrip, QFileDialog, QMessageBox, QMenu, QSplitter, QTextBrowser,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile, QWebEnginePage, QWebEngineSettings,
    QWebEngineScript, QWebEngineUrlRequestInterceptor, QWebEngineDownloadRequest,
)
from PyQt6.QtNetwork import QNetworkProxy, QLocalServer, QLocalSocket


# ─────────────────────────────────────────────────────────────────────────
#  WIN32 ДЛЯ КАСТОМНОГО ЗАГОЛОВКА «КАК В CHROME» (нативные Snap/resize/тень)
# ─────────────────────────────────────────────────────────────────────────

IS_WIN = sys.platform == "win32"

if IS_WIN:
    from ctypes import wintypes

    GWL_STYLE = -16
    WS_CAPTION = 0x00C00000
    WS_THICKFRAME = 0x00040000
    WS_MINIMIZEBOX = 0x00020000
    WS_MAXIMIZEBOX = 0x00010000
    WS_SYSMENU = 0x00080000
    WM_NCCALCSIZE = 0x0083
    WM_NCHITTEST = 0x0084
    SM_CXSIZEFRAME, SM_CYSIZEFRAME, SM_CXPADDEDBORDER = 32, 33, 92
    (HTCLIENT, HTCAPTION, HTLEFT, HTRIGHT, HTTOP, HTTOPLEFT, HTTOPRIGHT,
     HTBOTTOM, HTBOTTOMLEFT, HTBOTTOMRIGHT) = (1, 2, 10, 11, 12, 13, 14, 15, 16, 17)

    class MARGINS(ctypes.Structure):
        _fields_ = [("cxLeftWidth", ctypes.c_int), ("cxRightWidth", ctypes.c_int),
                    ("cyTopHeight", ctypes.c_int), ("cyBottomHeight", ctypes.c_int)]

    class NCCALCSIZE_PARAMS(ctypes.Structure):
        _fields_ = [("rgrc", wintypes.RECT * 3), ("lppos", ctypes.c_void_p)]

    _user32 = ctypes.windll.user32
    _dwmapi = ctypes.windll.dwmapi
    _user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    _user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    _user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
    _user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
    _user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    _user32.GetWindowRect.restype = wintypes.BOOL
    _user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int,
                                     ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
    _user32.SetWindowPos.restype = wintypes.BOOL
    _user32.GetSystemMetrics.argtypes = [ctypes.c_int]
    _user32.GetSystemMetrics.restype = ctypes.c_int
    _dwmapi.DwmExtendFrameIntoClientArea.argtypes = [wintypes.HWND, ctypes.POINTER(MARGINS)]
    _dwmapi.DwmExtendFrameIntoClientArea.restype = ctypes.c_long


def apply_native_dark_titlebar(hwnd: int):
    """Тёмный цвет (скрытого) заголовка + скруглённые углы Windows 11 через DWM."""
    try:
        dwm = ctypes.windll.dwmapi
        sa = dwm.DwmSetWindowAttribute
        sa.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]

        def put(attr, value):
            v = ctypes.c_int(value)
            sa(hwnd, attr, ctypes.byref(v), ctypes.sizeof(v))

        put(20, 1)              # DWMWA_USE_IMMERSIVE_DARK_MODE
        put(35, 0x002E1E1E)     # DWMWA_CAPTION_COLOR  #1E1E2E (0x00BBGGRR) — прячет 1px-линию
        put(34, 0x00443231)     # DWMWA_BORDER_COLOR   #313244
        put(33, 2)              # DWMWA_WINDOW_CORNER_PREFERENCE = ROUND
    except Exception:
        pass


class DragBar(QWidget):
    """Полоска заголовка: тащим окно за пустую зону, двойной клик = развернуть/восстановить.
    Клики по дочерним (вкладки/кнопки) они забирают сами — сюда доходит только пустое место."""

    def __init__(self, win):
        super().__init__()
        self.win = win
        self._press = None

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._press = e.globalPosition().toPoint() - self.win.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):
        if self._press is not None and (e.buttons() & Qt.MouseButton.LeftButton):
            if self.win.is_maxed():
                return
            self.win.move(e.globalPosition().toPoint() - self._press)
            e.accept()

    def mouseReleaseEvent(self, e):
        self._press = None

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.win.toggle_max_restore()


class FramelessWindow(QMainWindow):
    """Стабильное frameless-окно БЕЗ хрупкого Win32: ручное перетаскивание за титул,
    разворачивание в рабочую область (не накрывая панель задач), скруглённые углы."""

    def __init__(self):
        super().__init__()
        self._titlestrip = None
        self._normal_geom = None
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

    def set_caption(self, strip, draggable=()):
        self._titlestrip = strip

    def is_maxed(self):
        return self._normal_geom is not None

    def toggle_max_restore(self):
        if self.is_maxed():
            g, self._normal_geom = self._normal_geom, None
            if g is not None:
                self.setGeometry(g)
        else:
            self._normal_geom = self.geometry()
            scr = self.screen() or QApplication.primaryScreen()
            if scr is not None:
                self.setGeometry(scr.availableGeometry())
        self.apply_rounded_mask()
        if hasattr(self, "btn_max"):
            self.btn_max.setText(GLYPH_RESTORE if self.is_maxed() else GLYPH_MAX)
            self.btn_max.setToolTip("Восстановить" if self.is_maxed() else "Развернуть")

    def apply_rounded_mask(self):
        from PyQt6.QtGui import QPainterPath, QRegion
        if self.is_maxed() or self.isFullScreen():
            self.clearMask()
            return
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, float(self.width()), float(self.height())), 12, 12)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.apply_rounded_mask()


# ─────────────────────────────────────────────────────────────────────────
#  КОНСТАНТЫ И ХРАНИЛИЩЕ
# ─────────────────────────────────────────────────────────────────────────

TOR_HOST, TOR_PORT = "127.0.0.1", 9050
# Tor demon слушает 9050, Tor Browser — 9150. Пробуем оба.
TOR_PORTS = (9050, 9150)


def find_tor_port(host=TOR_HOST, ports=TOR_PORTS, timeout=0.4):
    """Возвращает порт, на котором реально слушает Tor SOCKS5, или None.
    Без этой проверки включение Ghost Mode при выключенном Tor роняет
    весь интернет в браузере (трафик уходит в мёртвый прокси)."""
    for port in ports:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return port
        except OSError:
            continue
    return None
TOR_UA = "Mozilla/5.0 (Windows NT 10.0; rv:115.0) Gecko/20100101 Firefox/115.0"
NORMAL_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# ── НАША поисковая система ──
SEARCH_NAME = "Phantom Search"
SEARCH_QUERY_URL = "https://duckduckgo.com/?q={q}"   # приватный бэкенд (без слежки)
SEARCH_FORM_ACTION = "https://duckduckgo.com/"

INTERNAL_PREFIX = "https://phantom."
HOME_URL = "https://phantom.start/"
HISTORY_URL = "https://phantom.history/"

AI_MODEL = "claude-sonnet-4-6"
AI_API_URL = "https://api.anthropic.com/v1/messages"

# Глифы кнопок окна (шрифт Segoe Fluent Icons / Segoe MDL2 Assets — как в Windows)
GLYPH_MIN, GLYPH_MAX, GLYPH_RESTORE, GLYPH_CLOSE = "\uE921", "\uE922", "\uE923", "\uE8BB"


def data_dir() -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "PhantomBrowser")
    os.makedirs(d, exist_ok=True)
    return d


DATA_DIR = data_dir()
BOOKMARKS_FILE = os.path.join(DATA_DIR, "bookmarks.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
SESSION_FILE = os.path.join(DATA_DIR, "session.json")
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, obj):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def is_internal(url: str) -> bool:
    return (not url) or url == "about:blank" or url.startswith(INTERNAL_PREFIX)


def smart_url(text: str) -> QUrl:
    """Текст из Omnibox → QUrl. URL дополняется схемой, иначе — Phantom Search."""
    text = text.strip()
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://", text) or text.startswith("about:"):
        return QUrl(text)
    host = text.split("/", 1)[0]
    if (" " not in text) and ("." in text or host.startswith("localhost")):
        is_local = host.startswith("localhost") or re.match(r"^(\d{1,3}\.){3}\d{1,3}", host)
        return QUrl(("http://" if is_local else "https://") + text)
    return QUrl(SEARCH_QUERY_URL.replace("{q}", urllib.parse.quote_plus(text)))


# ─────────────────────────────────────────────────────────────────────────
#  БЛОКИРОВЩИК ТРЕКЕРОВ
# ─────────────────────────────────────────────────────────────────────────

class AdBlocker(QWebEngineUrlRequestInterceptor):
    blocked = pyqtSignal(str)
    BLOCKLIST = (
        "doubleclick.net", "google-analytics.com", "googlesyndication.com",
        "googletagmanager.com", "googletagservices.com", "adservice.google.com",
        "analytics.google.com", "ads.yahoo.com", "scorecardresearch.com",
        "adnxs.com", "criteo.com", "taboola.com", "outbrain.com",
    )

    def interceptRequest(self, info):
        host = info.requestUrl().host()
        for domain in self.BLOCKLIST:
            if host == domain or host.endswith("." + domain):
                info.block(True)
                self.blocked.emit(host)
                return


# ─────────────────────────────────────────────────────────────────────────
#  WEB-VIEW
# ─────────────────────────────────────────────────────────────────────────

class WebView(QWebEngineView):
    def __init__(self, browser: "Browser"):
        super().__init__()
        self.browser = browser

    def createWindow(self, _type):
        return self.browser.add_tab(load_home=False)


class OmniBox(QLineEdit):
    def __init__(self, *a):
        super().__init__(*a)
        self._eff = QGraphicsDropShadowEffect(self)
        self._eff.setOffset(0, 0)
        self._eff.setBlurRadius(0)
        self._eff.setColor(QColor("#89B4FA"))
        self.setGraphicsEffect(self._eff)
        self._an = QPropertyAnimation(self._eff, b"blurRadius", self)
        self._an.setDuration(240)
        self._an.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _glow(self, v):
        self._an.stop()
        self._an.setEndValue(float(v))
        self._an.start()

    def focusInEvent(self, e):
        super().focusInEvent(e)
        QTimer.singleShot(0, self.selectAll)
        self._glow(28)

    def focusOutEvent(self, e):
        super().focusOutEvent(e)
        self._glow(0)


class HoverGlow(QObject):
    """Плавное свечение-ореол вокруг кнопки при наведении (анимация blurRadius)."""

    def __init__(self, widget, color="#89B4FA", strength=22):
        super().__init__(widget)
        self.strength = strength
        eff = QGraphicsDropShadowEffect(widget)
        eff.setOffset(0, 0)
        eff.setBlurRadius(0)
        eff.setColor(QColor(color))
        widget.setGraphicsEffect(eff)
        self.anim = QPropertyAnimation(eff, b"blurRadius", self)
        self.anim.setDuration(180)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        widget.installEventFilter(self)

    def eventFilter(self, obj, e):
        t = e.type()
        if t == QEvent.Type.Enter:
            self._to(self.strength)
        elif t == QEvent.Type.Leave:
            self._to(0)
        return False

    def _to(self, value):
        self.anim.stop()
        self.anim.setEndValue(float(value))
        self.anim.start()


def attach_glow(widget, color="#89B4FA"):
    HoverGlow(widget, color)
    return widget


# ─────────────────────────────────────────────────────────────────────────
#  ПОИСК ПО СТРАНИЦЕ (Ctrl+F)
# ─────────────────────────────────────────────────────────────────────────

class FindBar(QFrame):
    def __init__(self, browser: "Browser"):
        super().__init__()
        self.browser = browser
        self.setObjectName("FindBar")
        self.hide()
        h = QHBoxLayout(self)
        h.setContentsMargins(12, 6, 12, 6)
        h.setSpacing(6)
        self.inp = QLineEdit()
        self.inp.setObjectName("FindInput")
        self.inp.setPlaceholderText("Поиск на странице…")
        self.inp.textChanged.connect(lambda t: self.browser.find_text(t, True))
        self.inp.returnPressed.connect(lambda: self.browser.find_text(self.inp.text(), True))
        h.addWidget(QLabel("🔎"))
        h.addWidget(self.inp, 1)
        for glyph, fwd, tip in (("˄", False, "Назад"), ("˅", True, "Вперёд")):
            b = QPushButton(glyph)
            b.setObjectName("FindBtn")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setToolTip(tip)
            b.clicked.connect(lambda _, f=fwd: self.browser.find_text(self.inp.text(), f))
            h.addWidget(b)
        close = QPushButton("✕")
        close.setObjectName("FindBtn")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.clicked.connect(self.close_bar)
        h.addWidget(close)
        e = QShortcut(QKeySequence("Escape"), self)
        e.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        e.activated.connect(self.close_bar)

    def open_bar(self):
        self.show()
        self.inp.setFocus()
        self.inp.selectAll()
        self._slide_to(46)

    def close_bar(self):
        self.browser.find_text("", True)
        self._slide_to(0, hide=True)

    def _slide_to(self, h, hide=False):
        cur = self.maximumHeight()
        if cur > 1000:
            cur = self.height() if self.isVisible() else 0
        a = QPropertyAnimation(self, b"maximumHeight", self)
        a.setDuration(190)
        a.setEasingCurve(QEasingCurve.Type.InOutCubic)
        a.setStartValue(int(cur))
        a.setEndValue(int(h))
        if hide:
            a.finished.connect(self.hide)
        self._slide = a
        a.start()


# ─────────────────────────────────────────────────────────────────────────
#  AI: воркер + панель (фича «Comet»)
# ─────────────────────────────────────────────────────────────────────────

class AiWorker(QThread):
    done = pyqtSignal(str)
    fail = pyqtSignal(str)

    def __init__(self, api_key, model, messages, system_blocks):
        super().__init__()
        self.api_key, self.model = api_key, model
        self.messages, self.system = messages, system_blocks

    def run(self):
        try:
            payload = {"model": self.model, "max_tokens": 1200,
                       "system": self.system, "messages": self.messages}
            req = urllib.request.Request(
                AI_API_URL, data=json.dumps(payload).encode("utf-8"),
                headers={"content-type": "application/json", "x-api-key": self.api_key,
                         "anthropic-version": "2023-06-01"}, method="POST")
            with urllib.request.urlopen(req, timeout=90) as r:
                obj = json.loads(r.read().decode("utf-8"))
            text = "".join(b.get("text", "") for b in obj.get("content", [])
                           if b.get("type") == "text").strip()
            self.done.emit(text or "(пустой ответ)")
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", "ignore")
            except Exception:
                body = ""
            self.fail.emit(f"HTTP {e.code}. {body[:300]}")
        except Exception as e:  # noqa: BLE001
            self.fail.emit(f"{type(e).__name__}: {e}")


class AiPanel(QFrame):
    SYSTEM = ("Ты — встроенный AI-ассистент браузера Phantom. Пользователь смотрит "
              "веб-страницу, её содержимое приведено ниже. Отвечай кратко, по делу, "
              "на языке пользователя. Если вопрос о странице — опирайся на её текст.")

    def __init__(self, browser: "Browser"):
        super().__init__()
        self.browser = browser
        self.setObjectName("AiPanel")
        self.setMinimumWidth(320)
        self.setMaximumWidth(560)
        self.conv = []
        self.pending = False
        self.worker = None

        v = QVBoxLayout(self)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(10)
        head = QHBoxLayout()
        title = QLabel("✨ AI Assistant")
        title.setObjectName("AiTitle")
        head.addWidget(title)
        head.addStretch(1)
        x = QPushButton("✕")
        x.setObjectName("WinClose")
        x.setFixedSize(34, 28)
        x.setCursor(Qt.CursorShape.PointingHandCursor)
        x.clicked.connect(lambda: self.browser.toggle_ai(False))
        head.addWidget(x)
        v.addLayout(head)

        self.view = QTextBrowser()
        self.view.setObjectName("AiView")
        self.view.setOpenLinks(False)
        v.addWidget(self.view, 1)

        sumb = QPushButton("📄 Резюме этой страницы")
        sumb.setObjectName("AiSumBtn")
        sumb.setCursor(Qt.CursorShape.PointingHandCursor)
        sumb.clicked.connect(self.summarize)
        v.addWidget(sumb)

        row = QHBoxLayout()
        row.setSpacing(6)
        self.inp = QLineEdit()
        self.inp.setObjectName("AiInput")
        self.inp.setPlaceholderText("Спроси о странице…")
        self.inp.returnPressed.connect(self.send)
        send = QPushButton("▶")
        send.setObjectName("AiSendBtn")
        send.setCursor(Qt.CursorShape.PointingHandCursor)
        send.clicked.connect(self.send)
        row.addWidget(self.inp, 1)
        row.addWidget(send)
        v.addLayout(row)

        self.model_lbl = QLabel(f"модель: {AI_MODEL}")
        self.model_lbl.setObjectName("AiModel")
        v.addWidget(self.model_lbl)
        self._welcome()

    def _welcome(self):
        self.conv = [{"role": "assistant",
                      "content": "Привет! Я вижу открытую страницу. Спроси что-нибудь "
                                 "или нажми «Резюме этой страницы». 🚀"}]
        self._render()

    def _render(self):
        rows = []
        for m in self.conv:
            user = m["role"] == "user"
            who = "Вы" if user else "AI"
            color = "#89B4FA" if user else "#A6E3A1"
            body = esc(m["content"]).replace("\n", "<br>")
            rows.append(f'<p style="margin:7px 0;line-height:1.45">'
                        f'<b style="color:{color}">{who}:</b> '
                        f'<span style="color:#CDD6F4">{body}</span></p>')
        if self.pending:
            rows.append('<p style="color:#6C7086"><i>AI думает…</i></p>')
        self.view.setHtml("<div style='font-family:Segoe UI'>" + "".join(rows) + "</div>")
        QTimer.singleShot(0, lambda: self.view.verticalScrollBar().setValue(
            self.view.verticalScrollBar().maximum()))

    def summarize(self):
        self.inp.setText("Сделай краткое резюме этой страницы по пунктам.")
        self.send()

    def send(self):
        q = self.inp.text().strip()
        if not q or self.pending:
            return
        self.conv.append({"role": "user", "content": q})
        self.inp.clear()
        self.pending = True
        self._render()
        v = self.browser.current_view()
        url = v.url().toString() if v else ""
        if v:
            v.page().toPlainText(lambda txt: self._call(url, txt or ""))
        else:
            self._call(url, "")

    def _call(self, url, page_text):
        key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not key:
            self.pending = False
            self.conv.append({"role": "assistant", "content":
                "⚠️ Не задан ключ ANTHROPIC_API_KEY.\n\nЗадай его и перезапусти браузер:\n"
                "PowerShell:  setx ANTHROPIC_API_KEY \"sk-ant-...\"\n"
                "Ключ берётся на console.anthropic.com"})
            self._render()
            return
        system = [
            {"type": "text", "text": self.SYSTEM},
            {"type": "text",
             "text": f"URL страницы: {url}\n\nТЕКСТ СТРАНИЦЫ:\n{page_text[:14000]}",
             "cache_control": {"type": "ephemeral"}},
        ]
        msgs = [{"role": m["role"], "content": m["content"]} for m in self.conv]
        self.worker = AiWorker(key, AI_MODEL, msgs, system)
        self.worker.done.connect(self._on_done)
        self.worker.fail.connect(self._on_fail)
        self.worker.start()

    def _on_done(self, text):
        self.pending = False
        self.conv.append({"role": "assistant", "content": text})
        self._render()

    def _on_fail(self, err):
        self.pending = False
        self.conv.append({"role": "assistant", "content": "❌ Ошибка запроса: " + err})
        self._render()


# ─────────────────────────────────────────────────────────────────────────
#  ГЛАВНОЕ ОКНО — Chrome-style
# ─────────────────────────────────────────────────────────────────────────

class Browser(FramelessWindow):

    def __init__(self):
        super().__init__()
        self.ad_count = 0
        self._levitation = None
        self.bookmarks = load_json(BOOKMARKS_FILE, [])
        self.history = load_json(HISTORY_FILE, [])

        self.setWindowTitle("Phantom Browser")
        self.setMinimumSize(960, 640)
        self.resize(1340, 850)

        self._build_profiles()
        self._build_ui()
        self._build_shortcuts()
        self._restore_session()
        self.update_status()

    # ── Профили ──────────────────────────────────────────────────────────
    def _build_profiles(self):
        self.adblocker = AdBlocker()
        self.adblocker.blocked.connect(self._on_ad_blocked)
        self.profile_normal = QWebEngineProfile("PhantomNormal", self)
        self.profile_ghost = QWebEngineProfile(self)
        for profile, ua in ((self.profile_normal, NORMAL_UA), (self.profile_ghost, TOR_UA)):
            profile.setHttpUserAgent(ua)
            profile.setUrlRequestInterceptor(self.adblocker)
            profile.downloadRequested.connect(self._on_download)
            self._install_scrollbar_script(profile)
        self.active_profile = self.profile_normal

    def _install_scrollbar_script(self, profile):
        js = """
        (function(){ if(document.getElementById('phantom-sb'))return;
          var s=document.createElement('style');s.id='phantom-sb';
          s.textContent=`::-webkit-scrollbar{width:12px;height:12px;}
            ::-webkit-scrollbar-track{background:#181825;}
            ::-webkit-scrollbar-thumb{background:#45475A;border-radius:8px;border:3px solid #181825;}
            ::-webkit-scrollbar-thumb:hover{background:#89B4FA;}
            ::-webkit-scrollbar-corner{background:#181825;}`;
          (document.head||document.documentElement).appendChild(s);})();
        """
        sc = QWebEngineScript()
        sc.setName("phantom-scrollbars")
        sc.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        sc.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        sc.setRunsOnSubFrames(True)
        sc.setSourceCode(js)
        profile.scripts().insert(sc)

    # ── Интерфейс ────────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        central.setObjectName("Central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── РЯД 0: ВКЛАДКИ В ЗАГОЛОВКЕ (Chrome-style) + кнопки окна ──
        self.titlestrip = DragBar(self)
        self.titlestrip.setObjectName("TitleStrip")
        self.titlestrip.setFixedHeight(40)
        ts = QHBoxLayout(self.titlestrip)
        ts.setContentsMargins(8, 0, 0, 0)
        ts.setSpacing(0)

        self.logo = QLabel("◆")
        self.logo.setObjectName("LogoMark")
        ts.addWidget(self.logo)

        self.tabbar = QTabBar()
        self.tabbar.setObjectName("ChromeTabs")
        self.tabbar.setTabsClosable(True)
        self.tabbar.setMovable(True)
        self.tabbar.setExpanding(False)
        self.tabbar.setDrawBase(False)
        self.tabbar.setUsesScrollButtons(True)
        self.tabbar.setElideMode(Qt.TextElideMode.ElideRight)
        self.tabbar.currentChanged.connect(self.on_tab_changed)
        self.tabbar.tabCloseRequested.connect(self.close_tab)
        ts.addWidget(self.tabbar)

        self.newtab_btn = QPushButton("+")
        self.newtab_btn.setObjectName("NewTabBtn")
        self.newtab_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.newtab_btn.setToolTip("Новая вкладка (Ctrl+T)")
        self.newtab_btn.clicked.connect(lambda: self.add_tab())
        ts.addWidget(self.newtab_btn)

        ts.addStretch(1)   # пустая зона = тащим окно (HTCAPTION)

        for obj, glyph, slot, tip in (
                ("WinMin", GLYPH_MIN, self.showMinimized, "Свернуть"),
                ("WinMax", GLYPH_MAX, self.toggle_max_restore, "Развернуть"),
                ("WinClose", GLYPH_CLOSE, self.close, "Закрыть")):
            b = QPushButton(glyph)
            b.setObjectName(obj)
            b.setFixedSize(46, 40)
            b.clicked.connect(slot)
            ts.addWidget(b)
            if obj == "WinMax":
                self.btn_max = b
        root.addWidget(self.titlestrip)
        self.set_caption(self.titlestrip, (self.titlestrip, self.logo))

        # ── РЯД 1: ТУЛБАР ──
        toolbar = QWidget()
        toolbar.setObjectName("Toolbar")
        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(10, 7, 10, 7)
        tl.setSpacing(6)
        self.btn_back = self._mk_btn("←", "NavBtn", self.nav_back, "Назад (Alt+←)")
        self.btn_fwd = self._mk_btn("→", "NavBtn", self.nav_forward, "Вперёд (Alt+→)")
        self.btn_reload = self._mk_btn("⟳", "NavBtn", self.nav_reload, "Обновить (F5)")
        btn_home = self._mk_btn("⌂", "NavBtn", self.nav_home, "Домой")
        for b in (self.btn_back, self.btn_fwd, self.btn_reload, btn_home):
            tl.addWidget(b)

        self.omnibox = OmniBox()
        self.omnibox.setObjectName("Omnibox")
        self.omnibox.setPlaceholderText(f"Поиск в {SEARCH_NAME} или ввод адреса…  (попробуй «antigravity»)")
        self.omnibox.setClearButtonEnabled(True)
        self.omnibox.returnPressed.connect(lambda: self.navigate(self.omnibox.text()))
        tl.addWidget(self.omnibox, 1)

        tl.addWidget(self._mk_btn("⭐", "NavBtn", self.add_bookmark, "В закладки (Ctrl+D)"))
        self.ai_btn = self._mk_btn("✨ AI", "AiBtn", lambda: self.toggle_ai(), "AI-ассистент")
        tl.addWidget(self.ai_btn)
        self.ghost_btn = QPushButton("🌙 Ghost Mode")
        self.ghost_btn.setObjectName("GhostBtn")
        self.ghost_btn.setCheckable(True)
        self.ghost_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ghost_btn.setToolTip("Tor SOCKS5 + спуфинг UA + инкогнито-профиль")
        self.ghost_btn.toggled.connect(self.toggle_ghost)
        HoverGlow(self.ghost_btn, "#A6E3A1")
        tl.addWidget(self.ghost_btn)
        tl.addWidget(self._mk_btn("🚀", "AntiBtn", self.antigravity, "Antigravity"))
        tl.addWidget(self._mk_btn("⋮", "NavBtn", self.open_menu, "Меню"))
        root.addWidget(toolbar)

        # Панель закладок
        self.bookmark_bar = QWidget()
        self.bookmark_bar.setObjectName("BookmarkBar")
        self.bm_layout = QHBoxLayout(self.bookmark_bar)
        self.bm_layout.setContentsMargins(10, 2, 10, 4)
        self.bm_layout.setSpacing(5)
        root.addWidget(self.bookmark_bar)

        # Прогресс
        self.progress = QProgressBar()
        self.progress.setObjectName("Progress")
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(3)
        self.progress.hide()
        root.addWidget(self.progress)

        # Тело: [ стек страниц | AI-панель ]
        self.stack = QStackedWidget()
        self.stack.setObjectName("Stack")
        self.ai_panel = AiPanel(self)
        self.ai_panel.hide()
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setObjectName("Body")
        self.splitter.setHandleWidth(2)
        self.splitter.addWidget(self.stack)
        self.splitter.addWidget(self.ai_panel)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.setCollapsible(0, False)
        root.addWidget(self.splitter, 1)

        # Поиск по странице
        self.findbar = FindBar(self)
        root.addWidget(self.findbar)

        # Статус-бар + ресайз-грип
        sb = QWidget()
        sb.setObjectName("StatusBar")
        sl = QHBoxLayout(sb)
        sl.setContentsMargins(12, 0, 4, 2)
        sl.setSpacing(0)
        self.status = QLabel("")
        self.status.setObjectName("StatusText")
        sl.addWidget(self.status)
        sl.addStretch(1)
        sl.addWidget(QSizeGrip(sb), 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        sb.setFixedHeight(24)
        root.addWidget(sb)

        self._refresh_bookmarks()

    def _mk_btn(self, text, obj, slot, tip=""):
        b = QPushButton(text)
        b.setObjectName(obj)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        if tip:
            b.setToolTip(tip)
        b.clicked.connect(slot)
        glow = "#CBA6F7" if obj == "AntiBtn" else "#89B4FA"
        HoverGlow(b, glow)            # плавное свечение при наведении
        return b

    def _build_shortcuts(self):
        sc = lambda keys, fn: QShortcut(QKeySequence(keys), self).activated.connect(fn)
        sc("Ctrl+T", lambda: self.add_tab())
        sc("Ctrl+W", lambda: self.close_tab(self.tabbar.currentIndex()))
        sc("Ctrl+L", self._focus_omnibox)
        sc("Ctrl+R", self.nav_reload)
        sc("F5", self.nav_reload)
        sc("Alt+Left", self.nav_back)
        sc("Alt+Right", self.nav_forward)
        sc("F11", self._toggle_fullscreen)
        sc("Ctrl+F", lambda: self.findbar.open_bar())
        sc("Ctrl+D", self.add_bookmark)
        sc("Ctrl+H", self.show_history)
        sc("Ctrl+Shift+B", self._toggle_bookmark_bar)
        sc("Ctrl+J", lambda: os.startfile(DOWNLOADS_DIR) if os.path.isdir(DOWNLOADS_DIR) else None)
        sc("Ctrl+=", lambda: self.zoom(+0.1))
        sc("Ctrl++", lambda: self.zoom(+0.1))
        sc("Ctrl+-", lambda: self.zoom(-0.1))
        sc("Ctrl+0", self.zoom_reset)

    # ── Вкладки (QTabBar + QStackedWidget, связка через tabData) ──────────
    def add_tab(self, url=None, load_home=True, switch=True) -> WebView:
        view = WebView(self)
        view.setPage(QWebEnginePage(self.active_profile, view))
        self._configure_page(view)
        view.urlChanged.connect(lambda u, v=view: self._on_url_changed(v, u))
        view.loadStarted.connect(lambda v=view: self._on_load_started(v))
        view.loadProgress.connect(lambda p, v=view: self._on_load_progress(v, p))
        view.loadFinished.connect(lambda ok, v=view: self._on_load_finished(v, ok))
        view.titleChanged.connect(lambda t, v=view: self._on_title_changed(v, t))
        view.iconChanged.connect(lambda ic, v=view: self._on_icon_changed(v, ic))
        self.stack.addWidget(view)
        idx = self.tabbar.addTab("Новая вкладка")
        self.tabbar.setTabData(idx, view)
        if switch:
            self.tabbar.setCurrentIndex(idx)
            self.stack.setCurrentWidget(view)
        if url:
            view.setUrl(QUrl(url) if isinstance(url, str) else url)
        elif load_home:
            self.load_start_page(view)
        return view

    def _configure_page(self, view):
        s = view.settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        view.page().fullScreenRequested.connect(self._on_fullscreen)

    def _tab_index(self, view):
        for i in range(self.tabbar.count()):
            if self.tabbar.tabData(i) is view:
                return i
        return -1

    def close_tab(self, index: int):
        if index < 0 or index >= self.tabbar.count():
            return
        view = self.tabbar.tabData(index)
        self.tabbar.removeTab(index)
        if isinstance(view, WebView):
            self.stack.removeWidget(view)
            view.deleteLater()
        if self.tabbar.count() == 0:
            self.add_tab()
        else:
            cur = self.tabbar.tabData(self.tabbar.currentIndex())
            if isinstance(cur, WebView):
                self.stack.setCurrentWidget(cur)

    def current_view(self):
        i = self.tabbar.currentIndex()
        if i < 0:
            return None
        v = self.tabbar.tabData(i)
        return v if isinstance(v, WebView) else None

    def load_start_page(self, view):
        view.setHtml(START_PAGE, QUrl(HOME_URL))

    # ── Навигация ────────────────────────────────────────────────────────
    def navigate(self, text: str):
        text = text.strip()
        if not text:
            return
        if text.lower() == "antigravity":
            self.antigravity()
            return
        view = self.current_view() or self.add_tab(load_home=False)
        view.setUrl(smart_url(text))

    def nav_back(self):
        v = self.current_view()
        v and v.back()

    def nav_forward(self):
        v = self.current_view()
        v and v.forward()

    def nav_reload(self):
        v = self.current_view()
        v and v.reload()

    def nav_home(self):
        v = self.current_view()
        self.load_start_page(v) if v else self.add_tab()

    def _focus_omnibox(self):
        self.omnibox.setFocus()
        self.omnibox.selectAll()

    def zoom(self, d):
        v = self.current_view()
        if v:
            v.setZoomFactor(max(0.3, min(3.0, v.zoomFactor() + d)))

    def zoom_reset(self):
        v = self.current_view()
        if v:
            v.setZoomFactor(1.0)

    def find_text(self, text, forward=True):
        v = self.current_view()
        if not v:
            return
        if forward:
            v.findText(text)
        else:
            v.findText(text, QWebEnginePage.FindFlag.FindBackward)

    # ── Сигналы движка ───────────────────────────────────────────────────
    def _on_url_changed(self, view, url):
        if view is self.current_view():
            s = url.toString()
            self.omnibox.setText("" if is_internal(s) else s)
            self._update_nav_buttons()

    def _on_load_started(self, view):
        if view is self.current_view():
            self.progress.setValue(3)
            self.progress.show()

    def _on_load_progress(self, view, p):
        if view is self.current_view():
            self.progress.show()
            self.progress.setValue(p)

    def _on_load_finished(self, view, ok):
        if view is self.current_view():
            self.progress.setValue(100)
            QTimer.singleShot(350, self.progress.hide)
            self._update_nav_buttons()
        idx = self._tab_index(view)
        if idx >= 0 and not self.tabbar.tabText(idx).strip():
            self.tabbar.setTabText(idx, "Без названия")
        if ok:
            self._record_history(view.url().toString(), view.title())

    def _on_title_changed(self, view, title):
        idx = self._tab_index(view)
        if idx < 0:
            return
        short = (title[:22] + "…") if len(title) > 23 else (title or "Новая вкладка")
        self.tabbar.setTabText(idx, short)
        if view is self.current_view():
            self.setWindowTitle(f"{title} — Phantom" if title else "Phantom Browser")

    def _on_icon_changed(self, view, icon):
        idx = self._tab_index(view)
        if idx >= 0:
            self.tabbar.setTabIcon(idx, icon)

    def _on_fullscreen(self, request):
        request.accept()
        self.showFullScreen() if request.toggleOn() else self.showNormal()

    def _on_ad_blocked(self, host):
        self.ad_count += 1
        self.update_status()

    def on_tab_changed(self, index):
        v = self.current_view()
        if v:
            self.stack.setCurrentWidget(v)
        self.progress.hide()
        if v:
            url = v.url().toString()
            self.omnibox.setText("" if is_internal(url) else url)
            t = v.title()
            self.setWindowTitle(f"{t} — Phantom" if t else "Phantom Browser")
        self._update_nav_buttons()

    def _update_nav_buttons(self):
        v = self.current_view()
        if v:
            h = v.history()
            self.btn_back.setEnabled(h.canGoBack())
            self.btn_fwd.setEnabled(h.canGoForward())
        else:
            self.btn_back.setEnabled(False)
            self.btn_fwd.setEnabled(False)

    # ── Загрузки ─────────────────────────────────────────────────────────
    def _on_download(self, item):
        suggested = item.downloadFileName()
        start = item.downloadDirectory() or DOWNLOADS_DIR
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", os.path.join(start, suggested))
        if not path:
            item.cancel()
            return
        item.setDownloadDirectory(os.path.dirname(path))
        item.setDownloadFileName(os.path.basename(path))
        item.accept()
        name = os.path.basename(path)
        item.receivedBytesChanged.connect(lambda it=item, n=name: self._dl_progress(it, n))
        item.isFinishedChanged.connect(lambda it=item, n=name: self._dl_finished(it, n))

    def _dl_progress(self, item, name):
        tot, rec = item.totalBytes(), item.receivedBytes()
        pct = int(rec * 100 / tot) if tot > 0 else 0
        self.status.setText(f"⬇ {name} — {pct}%  ({rec // 1024} КБ)")

    def _dl_finished(self, item, name):
        ok = item.state() == QWebEngineDownloadRequest.DownloadState.DownloadCompleted
        self.status.setText(f"✅ Загружено: {name}" if ok else f"⚠ Прервано: {name}")
        QTimer.singleShot(4000, self.update_status)

    # ── Закладки ─────────────────────────────────────────────────────────
    def add_bookmark(self):
        v = self.current_view()
        if not v:
            return
        url = v.url().toString()
        if is_internal(url):
            return
        if any(b["url"] == url for b in self.bookmarks):
            self.status.setText("Эта страница уже в закладках")
            QTimer.singleShot(2500, self.update_status)
            return
        self.bookmarks.append({"title": (v.title() or url)[:40], "url": url})
        save_json(BOOKMARKS_FILE, self.bookmarks)
        self._refresh_bookmarks()
        self.bookmark_bar.show()
        self.status.setText("⭐ Добавлено в закладки")
        QTimer.singleShot(2500, self.update_status)

    def _refresh_bookmarks(self):
        while self.bm_layout.count():
            it = self.bm_layout.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        for b in self.bookmarks:
            btn = QPushButton("🔖 " + b["title"])
            btn.setObjectName("BmBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(b["url"])
            btn.clicked.connect(lambda _, u=b["url"]: self.navigate(u))
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda _, bm=b: self._remove_bookmark(bm))
            self.bm_layout.addWidget(btn)
        self.bm_layout.addStretch(1)
        self.bookmark_bar.setVisible(bool(self.bookmarks))

    def _remove_bookmark(self, bm):
        self.bookmarks = [b for b in self.bookmarks if b["url"] != bm["url"]]
        save_json(BOOKMARKS_FILE, self.bookmarks)
        self._refresh_bookmarks()

    def _toggle_bookmark_bar(self):
        self.bookmark_bar.setVisible(not self.bookmark_bar.isVisible())

    # ── История ──────────────────────────────────────────────────────────
    def _record_history(self, url, title):
        if self.active_profile is self.profile_ghost or is_internal(url):
            return
        if self.history and self.history[-1].get("url") == url:
            return
        self.history.append({"title": title or url, "url": url, "ts": int(time.time())})
        self.history = self.history[-1000:]
        save_json(HISTORY_FILE, self.history)

    def show_history(self):
        rows = []
        for h in reversed(self.history[-400:]):
            when = time.strftime("%d.%m %H:%M", time.localtime(h.get("ts", 0)))
            rows.append(f'<a class="row" href="{esc(h["url"])}">'
                        f'<span class="t">{esc(h["title"])}</span>'
                        f'<span class="u">{esc(h["url"])}</span>'
                        f'<span class="d">{when}</span></a>')
        html = HISTORY_HEAD + ("".join(rows) or "<p style='color:#6C7086'>История пуста</p>") + HISTORY_TAIL
        v = self.current_view() or self.add_tab(load_home=False)
        v.setHtml(html, QUrl(HISTORY_URL))

    # ── AI-панель ────────────────────────────────────────────────────────
    def toggle_ai(self, show=None):
        if show is None:
            show = not self.ai_panel.isVisible()
        self.ai_btn.setProperty("active", "true" if show else "")
        self.ai_btn.style().unpolish(self.ai_btn)
        self.ai_btn.style().polish(self.ai_btn)

        target = 380 if show else 0
        total = max(self.splitter.width(), 800)
        start_w = self.ai_panel.width() if self.ai_panel.isVisible() else 0
        if show:
            self.ai_panel.setMaximumWidth(560)
            self.ai_panel.show()
            self.ai_panel.inp.setFocus()

        anim = QVariantAnimation(self)
        anim.setDuration(240)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim.setStartValue(float(start_w))
        anim.setEndValue(float(target))
        anim.valueChanged.connect(
            lambda v: self.splitter.setSizes([max(300, total - int(v)), int(v)]))

        def fin():
            if not show:
                self.ai_panel.hide()
        anim.finished.connect(fin)
        self._ai_anim = anim          # держим ссылку
        anim.start()

    # ── GHOST MODE ───────────────────────────────────────────────────────
    def toggle_ghost(self, on: bool):
        if on:
            # Сначала убеждаемся, что Tor реально запущен и слушает порт.
            # Иначе весь трафик уйдёт в мёртвый SOCKS5 и интернет в браузере
            # просто отвалится. Проверяем 9050 (демон) и 9150 (Tor Browser).
            port = find_tor_port()
            if port is None:
                self.ghost_btn.blockSignals(True)
                self.ghost_btn.setChecked(False)
                self.ghost_btn.blockSignals(False)
                box = QMessageBox(self)
                box.setIcon(QMessageBox.Icon.Warning)
                box.setWindowTitle("Tor не найден")
                box.setText("🧅  Ghost Mode не включён — Tor не запущен.")
                box.setInformativeText(
                    "Не удалось подключиться к Tor SOCKS5 на 127.0.0.1:9050 или :9150.\n\n"
                    "Запусти Tor и попробуй снова:\n"
                    "  • Tor Browser — открой его (слушает порт 9150), либо\n"
                    "  • демон tor — установи и запусти службу (порт 9050).\n\n"
                    "Без Tor включать прокси нельзя: интернет в браузере отвалится."
                )
                box.exec()
                return
            global TOR_PORT
            TOR_PORT = port
            proxy = QNetworkProxy(QNetworkProxy.ProxyType.Socks5Proxy, TOR_HOST, port)
            proxy.setCapabilities(QNetworkProxy.Capability.HostNameLookupCapability
                                  | QNetworkProxy.Capability.TunnelingCapability)
            QNetworkProxy.setApplicationProxy(proxy)
            self.active_profile = self.profile_ghost
            self.ghost_btn.setText("👻 Ghost: ON")
            self.logo.setText("👻")
        else:
            QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
            self.active_profile = self.profile_normal
            self.ghost_btn.setText("🌙 Ghost Mode")
            self.logo.setText("◆")
        self._rebuild_pages(self.active_profile)
        self.update_status()
        self._pulse_logo()

    def play_intro(self):
        """Плавное появление окна при запуске."""
        a = QPropertyAnimation(self, b"windowOpacity", self)
        a.setDuration(360)
        a.setStartValue(0.0)
        a.setEndValue(1.0)
        a.setEasingCurve(QEasingCurve.Type.OutCubic)
        a.start()
        self._intro = a
        QTimer.singleShot(560, lambda: self.setWindowOpacity(1.0))   # страховка видимости

    def _pulse_logo(self):
        """Пульс логотипа при смене режима."""
        eff = self.logo.graphicsEffect()
        if not isinstance(eff, QGraphicsOpacityEffect):
            eff = QGraphicsOpacityEffect(self.logo)
            self.logo.setGraphicsEffect(eff)
        a = QPropertyAnimation(eff, b"opacity", self)
        a.setDuration(440)
        a.setKeyValueAt(0.0, 1.0)
        a.setKeyValueAt(0.5, 0.15)
        a.setKeyValueAt(1.0, 1.0)
        self._logo_pulse = a
        a.start()

    def _rebuild_pages(self, profile):
        for i in range(self.stack.count()):
            view = self.stack.widget(i)
            if not isinstance(view, WebView):
                continue
            url = view.url()
            old = view.page()
            view.setPage(QWebEnginePage(profile, view))
            self._configure_page(view)
            if is_internal(url.toString()):
                self.load_start_page(view)
            else:
                view.setUrl(url)
            if old is not None:
                old.deleteLater()

    def update_status(self):
        if self.active_profile is self.profile_ghost:
            mode = f"👻 GHOST MODE — Tor SOCKS5 {TOR_HOST}:{TOR_PORT}  ·  Off-The-Record"
        else:
            mode = f"🌙 Стандартный режим  ·  поиск: {SEARCH_NAME}"
        self.status.setText(f"{mode}    ·    🛡 Трекеров заблокировано: {self.ad_count}")

    # ── Меню ─────────────────────────────────────────────────────────────
    def open_menu(self):
        m = QMenu(self)
        m.setObjectName("MainMenu")
        acts = [
            ("⭐  Добавить в закладки\tCtrl+D", self.add_bookmark),
            ("📑  Панель закладок\tCtrl+Shift+B", self._toggle_bookmark_bar),
            ("🕘  История\tCtrl+H", self.show_history),
            ("📁  Папка загрузок\tCtrl+J", lambda: os.startfile(DOWNLOADS_DIR)
                if os.path.isdir(DOWNLOADS_DIR) else None),
            ("🔎  Поиск на странице\tCtrl+F", lambda: self.findbar.open_bar()),
            (None, None),
            ("🌐  Сделать браузером по умолчанию", self.set_default_browser),
            ("ℹ️  О программе", self.about),
        ]
        for text, fn in acts:
            if text is None:
                m.addSeparator()
                continue
            a = QAction(text, self)
            a.triggered.connect(fn)
            m.addAction(a)
        m.exec(self.cursor().pos())

    def set_default_browser(self):
        try:
            os.startfile("ms-settings:defaultapps")
        except Exception:
            pass
        QMessageBox.information(
            self, "Браузер по умолчанию",
            "Открыл «Приложения по умолчанию» Windows.\n\n"
            "Windows 11 не даёт назначить браузер программно — только вручную.\n\n"
            "1) Собери .exe (build_exe.bat).\n"
            "2) Запусти set_default_browser.py — он зарегистрирует Phantom.\n"
            "3) Выбери Phantom для HTTP/HTTPS.")

    def about(self):
        QMessageBox.information(
            self, "Phantom Browser",
            "Phantom Browser v3\n\nPyQt6 · QtWebEngine (Chromium)\n"
            f"Вкладки в заголовке (Chrome-style) · {SEARCH_NAME} · Ghost (Tor) · AI · AdBlock\n\n"
            f"Данные: {DATA_DIR}")

    # ── 🚀 ANTIGRAVITY ───────────────────────────────────────────────────
    def antigravity(self):
        self.add_tab("https://xkcd.com/353/")
        self.levitate()

    def levitate(self):
        if self.isMaximized() or self.isFullScreen():
            self.showNormal()
        start = self.pos()
        amp = 48
        anim = QPropertyAnimation(self, b"pos", self)
        anim.setDuration(1300)
        anim.setLoopCount(2)
        anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        anim.setKeyValueAt(0.00, start)
        anim.setKeyValueAt(0.25, QPoint(start.x() + 7, start.y() - amp))
        anim.setKeyValueAt(0.50, QPoint(start.x() - 7, start.y() - amp // 3))
        anim.setKeyValueAt(0.75, QPoint(start.x() + 5, start.y() - amp))
        anim.setKeyValueAt(1.00, start)
        anim.finished.connect(lambda: self.move(start))
        self._levitation = anim
        anim.start()

    # ── Полноэкранный режим ──────────────────────────────────────────────
    def _toggle_fullscreen(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()
        self.apply_rounded_mask()

    # ── Сессия ───────────────────────────────────────────────────────────
    def _restore_session(self):
        urls = load_json(SESSION_FILE, {}).get("tabs", [])
        urls = [u for u in urls if u and not is_internal(u)]
        if urls:
            for u in urls:
                self.add_tab(u, switch=False)
            self.tabbar.setCurrentIndex(0)
            v = self.current_view()
            if v:
                self.stack.setCurrentWidget(v)
        else:
            self.add_tab()

    def _save_session(self):
        if self.active_profile is self.profile_ghost:
            return
        urls = []
        for i in range(self.stack.count()):
            v = self.stack.widget(i)
            if isinstance(v, WebView):
                s = v.url().toString()
                if s and not is_internal(s):
                    urls.append(s)
        save_json(SESSION_FILE, {"tabs": urls})

    def closeEvent(self, e):
        self._save_session()
        super().closeEvent(e)


# ─────────────────────────────────────────────────────────────────────────
#  СТАРТОВАЯ СТРАНИЦА с поиском Phantom Search
# ─────────────────────────────────────────────────────────────────────────

START_PAGE = """<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Phantom · New Tab</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',system-ui,sans-serif;}
  html,body{height:100%;}
  body{position:relative;min-height:100vh;display:flex;flex-direction:column;align-items:center;
       justify-content:center;gap:22px;background:#11111B;color:#CDD6F4;overflow:hidden;}
  /* анимированный фон-аврора + плавающие орбы */
  .bg{position:fixed;inset:0;z-index:-2;
       background:radial-gradient(900px 520px at 50% -8%,#313244 0%,#1E1E2E 55%,#11111B 100%);}
  .orb{position:fixed;border-radius:50%;filter:blur(72px);opacity:.5;z-index:-1;will-change:transform;
       animation:drift 18s ease-in-out infinite;}
  .orb.a{width:440px;height:440px;background:#89B4FA;left:-90px;top:-70px;}
  .orb.b{width:400px;height:400px;background:#CBA6F7;right:-110px;top:8%;animation-delay:-6s;}
  .orb.c{width:360px;height:360px;background:#A6E3A1;left:24%;bottom:-140px;animation-delay:-11s;opacity:.4;}
  @keyframes drift{0%,100%{transform:translate(0,0) scale(1);}
    33%{transform:translate(46px,34px) scale(1.1);}66%{transform:translate(-34px,22px) scale(.95);}}
  .clock{font-size:14px;color:#6C7086;letter-spacing:3px;opacity:0;animation:fadeUp .6s .05s forwards;}
  .logo{font-size:68px;font-weight:800;letter-spacing:8px;
        background:linear-gradient(100deg,#89B4FA,#CBA6F7,#A6E3A1,#89B4FA);background-size:300% 100%;
        -webkit-background-clip:text;background-clip:text;color:transparent;
        filter:drop-shadow(0 0 42px rgba(137,180,250,.32));
        animation:shimmer 7s linear infinite,floaty 5s ease-in-out infinite,popIn .8s cubic-bezier(.2,.9,.3,1.4) both;}
  @keyframes shimmer{to{background-position:300% 0;}}
  @keyframes floaty{0%,100%{transform:translateY(0);}50%{transform:translateY(-10px);}}
  @keyframes popIn{from{opacity:0;transform:scale(.8);}to{opacity:1;}}
  .sub{color:#A6ADC8;font-size:15px;margin-top:-10px;opacity:0;animation:fadeUp .7s .15s forwards;}
  @keyframes fadeUp{from{opacity:0;transform:translateY(16px);}to{opacity:1;transform:translateY(0);}}
  form.search{width:min(650px,82vw);position:relative;opacity:0;animation:fadeUp .7s .25s forwards;}
  form.search::before{content:"";position:absolute;inset:-2px;border-radius:30px;z-index:-1;filter:blur(15px);
        background:linear-gradient(120deg,#89B4FA,#CBA6F7,#A6E3A1);animation:breathe 4s ease-in-out infinite;}
  @keyframes breathe{0%,100%{opacity:.22;}50%{opacity:.5;}}
  form.search input{width:100%;padding:18px 22px;border-radius:28px;border:2px solid #313244;background:#181825;
        color:#CDD6F4;font-size:16px;outline:none;
        transition:border-color .25s,background .25s,transform .25s,box-shadow .25s;}
  form.search input:focus{border-color:#89B4FA;background:#11111B;transform:scale(1.025);
        box-shadow:0 14px 44px rgba(137,180,250,.30);}
  form.search:focus-within::before{animation:none;opacity:.75;}
  .ph{position:absolute;right:18px;top:16px;color:#585B70;font-size:12px;pointer-events:none;}
  .grid{display:grid;grid-template-columns:repeat(4,122px);gap:14px;}
  a.tile{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:9px;height:92px;
        border-radius:18px;text-decoration:none;color:#CDD6F4;background:rgba(49,50,68,.5);
        border:1px solid rgba(69,71,90,.6);backdrop-filter:blur(6px);font-size:12px;font-weight:600;
        opacity:0;transform:translateY(20px);animation:fadeUp .6s forwards;
        transition:transform .22s cubic-bezier(.2,.9,.3,1.3),border-color .22s,background .22s,box-shadow .22s;}
  .grid a:nth-child(1){animation-delay:.34s;}.grid a:nth-child(2){animation-delay:.40s;}
  .grid a:nth-child(3){animation-delay:.46s;}.grid a:nth-child(4){animation-delay:.52s;}
  .grid a:nth-child(5){animation-delay:.58s;}.grid a:nth-child(6){animation-delay:.64s;}
  .grid a:nth-child(7){animation-delay:.70s;}.grid a:nth-child(8){animation-delay:.76s;}
  a.tile:hover{transform:translateY(-7px) scale(1.06);border-color:#89B4FA;background:rgba(69,71,90,.88);
        box-shadow:0 16px 38px rgba(0,0,0,.45),0 0 24px rgba(137,180,250,.28);}
  a.tile .ico{font-size:28px;transition:transform .22s cubic-bezier(.2,.9,.3,1.5);}
  a.tile:hover .ico{transform:scale(1.28) translateY(-3px);}
  .foot{position:fixed;bottom:18px;color:#45475A;font-size:12px;opacity:0;animation:fadeUp 1s .85s forwards;}
  @media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important;}}
</style></head><body>
  <div class="bg"></div><div class="orb a"></div><div class="orb b"></div><div class="orb c"></div>
  <div class="clock" id="clock"></div>
  <div class="logo">PHANTOM</div>
  <div class="sub">Браузер нового поколения · Privacy-first · AI-native</div>
  <form class="search" action="__ACTION__" method="get" autocomplete="off">
    <input type="text" name="q" placeholder="Поиск в __NAME__…" autofocus>
    <span class="ph">⏎ Phantom Search</span>
  </form>
  <div class="grid">
    <a class="tile" href="https://github.com"><span class="ico">🐙</span>GitHub</a>
    <a class="tile" href="https://www.youtube.com"><span class="ico">▶️</span>YouTube</a>
    <a class="tile" href="https://news.ycombinator.com"><span class="ico">🟧</span>Hacker News</a>
    <a class="tile" href="https://check.torproject.org"><span class="ico">🧅</span>Tor Check</a>
    <a class="tile" href="https://xkcd.com/353/"><span class="ico">🚀</span>xkcd 353</a>
    <a class="tile" href="https://www.wikipedia.org"><span class="ico">📚</span>Wikipedia</a>
    <a class="tile" href="https://www.reddit.com"><span class="ico">👽</span>Reddit</a>
    <a class="tile" href="https://t.me"><span class="ico">✈️</span>Telegram</a>
  </div>
  <div class="foot">⚡ Powered by PyQt6 · QtWebEngine</div>
  <script>
    function tick(){var d=new Date(),h=d.getHours(),m=d.getMinutes();
      document.getElementById('clock').textContent=(h<10?'0':'')+h+':'+(m<10?'0':'')+m;}
    tick();setInterval(tick,1000);
  </script>
</body></html>""".replace("__ACTION__", SEARCH_FORM_ACTION).replace("__NAME__", SEARCH_NAME)

HISTORY_HEAD = """<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><title>История</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif;}
  body{background:#1E1E2E;color:#CDD6F4;padding:40px 60px;}
  h1{color:#89B4FA;font-size:28px;margin-bottom:22px;}
  a.row{display:flex;gap:18px;align-items:center;padding:11px 16px;border-radius:12px;
        text-decoration:none;color:#CDD6F4;border:1px solid transparent;}
  a.row:hover{background:#313244;border-color:#45475A;}
  .t{flex:0 0 320px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
  .u{flex:1;color:#6C7086;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
  .d{color:#585B70;font-size:12px;}
</style></head><body><h1>🕘 История посещений</h1>"""
HISTORY_TAIL = "</body></html>"


# ─────────────────────────────────────────────────────────────────────────
#  QSS (Catppuccin Mocha) — Chrome-style вкладки в заголовке
# ─────────────────────────────────────────────────────────────────────────

QSS = """
* { font-family: "Segoe UI", "Inter", sans-serif; outline: none; }
QWidget#Central { background: #1E1E2E; }
QStackedWidget#Stack { background: #1E1E2E; }

/* ── Заголовок с вкладками (Chrome-style) ── */
QWidget#TitleStrip { background: #181825; }
QLabel#LogoMark { color: #89B4FA; font-size: 18px; font-weight: 800; padding: 0 10px 0 4px; }

QTabBar#ChromeTabs { background: transparent; qproperty-drawBase: 0; }
QTabBar#ChromeTabs::tab {
    background: #232334; color: #A6ADC8; padding: 8px 14px; margin: 6px 2px 0 0;
    border-top-left-radius: 10px; border-top-right-radius: 10px;
    min-width: 120px; max-width: 240px; font-size: 12px; }
QTabBar#ChromeTabs::tab:hover { background: #313244; color: #CDD6F4; }
QTabBar#ChromeTabs::tab:selected { background: #1E1E2E; color: #CDD6F4; }
QTabBar#ChromeTabs::close-button { subcontrol-position: right; }
QTabBar::scroller { width: 18px; }

QPushButton#NewTabBtn {
    background: transparent; color: #A6ADC8; border: none; border-radius: 8px;
    font-size: 20px; font-weight: 600; min-width: 30px; min-height: 30px; margin-left: 4px; }
QPushButton#NewTabBtn:hover { background: #313244; color: #89B4FA; }

/* ── Кнопки окна (Segoe Fluent Icons — как в Windows 11) ── */
QPushButton#WinMin, QPushButton#WinMax, QPushButton#WinClose {
    background: transparent; color: #CDD6F4; border: none;
    font-family: "Segoe Fluent Icons", "Segoe MDL2 Assets"; font-size: 10px; }
QPushButton#WinMin:hover, QPushButton#WinMax:hover { background: #313244; }
QPushButton#WinClose:hover { background: #E81123; color: #FFFFFF; }

/* ── Тулбар ── */
QWidget#Toolbar { background: #1E1E2E; }
QPushButton#NavBtn {
    background: transparent; color: #CDD6F4; border: none; border-radius: 11px;
    font-size: 17px; min-width: 40px; min-height: 36px; }
QPushButton#NavBtn:hover { background: #313244; }
QPushButton#NavBtn:pressed { background: #45475A; }
QPushButton#NavBtn:disabled { color: #45475A; }

QLineEdit#Omnibox {
    background: #313244; color: #CDD6F4; border: 2px solid #313244; border-radius: 17px;
    padding: 8px 18px; font-size: 14px;
    selection-background-color: #89B4FA; selection-color: #11111B; }
QLineEdit#Omnibox:hover { border: 2px solid #45475A; }
QLineEdit#Omnibox:focus { border: 2px solid #89B4FA; background: #11111B; }

QPushButton#AiBtn {
    background: #313244; color: #89B4FA; border: 2px solid transparent; border-radius: 15px;
    padding: 7px 13px; font-weight: 700; }
QPushButton#AiBtn:hover { background: rgba(137,180,250,0.18); border: 2px solid #89B4FA; }
QPushButton#AiBtn[active="true"] { background: rgba(137,180,250,0.22); border: 2px solid #89B4FA; }
QPushButton#GhostBtn {
    background: #313244; color: #CDD6F4; border: 2px solid transparent; border-radius: 15px;
    padding: 7px 15px; font-weight: 600; }
QPushButton#GhostBtn:hover { background: #45475A; }
QPushButton#GhostBtn:checked { background: rgba(166,227,161,0.16); color: #A6E3A1; border: 2px solid #A6E3A1; }
QPushButton#AntiBtn {
    background: #313244; color: #CBA6F7; border: 2px solid transparent; border-radius: 15px;
    padding: 7px 13px; font-weight: 700; font-size: 15px; }
QPushButton#AntiBtn:hover { background: rgba(203,166,247,0.18); border: 2px solid #CBA6F7; }

QWidget#BookmarkBar { background: #1E1E2E; border-top: 1px solid #313244; }
QPushButton#BmBtn { background: transparent; color: #A6ADC8; border: none; border-radius: 8px;
    padding: 4px 10px; font-size: 12px; }
QPushButton#BmBtn:hover { background: #313244; color: #CDD6F4; }

QProgressBar#Progress { background: #181825; border: none; }
QProgressBar#Progress::chunk { background: #89B4FA; }
QSplitter#Body::handle { background: #181825; }

QFrame#FindBar { background: #181825; border-top: 1px solid #313244; }
QLineEdit#FindInput { background: #313244; color: #CDD6F4; border: 2px solid #313244;
    border-radius: 12px; padding: 5px 12px; }
QLineEdit#FindInput:focus { border: 2px solid #89B4FA; }
QPushButton#FindBtn { background: transparent; color: #A6ADC8; border: none; border-radius: 8px;
    min-width: 30px; min-height: 28px; font-size: 14px; }
QPushButton#FindBtn:hover { background: #313244; color: #CDD6F4; }

QFrame#AiPanel { background: #181825; border-left: 1px solid #313244; }
QLabel#AiTitle { color: #89B4FA; font-size: 15px; font-weight: 800; }
QLabel#AiModel { color: #45475A; font-size: 11px; }
QPushButton#WinClose { border-radius: 8px; }
QTextBrowser#AiView { background: #11111B; color: #CDD6F4; border: 1px solid #313244;
    border-radius: 12px; padding: 8px; font-size: 13px; }
QLineEdit#AiInput { background: #313244; color: #CDD6F4; border: 2px solid #313244;
    border-radius: 13px; padding: 8px 13px; }
QLineEdit#AiInput:focus { border: 2px solid #89B4FA; }
QPushButton#AiSendBtn { background: #89B4FA; color: #11111B; border: none; border-radius: 13px;
    font-weight: 800; min-width: 42px; min-height: 34px; }
QPushButton#AiSendBtn:hover { background: #B4CEFB; }
QPushButton#AiSumBtn { background: #313244; color: #CBA6F7; border: 1px solid #45475A;
    border-radius: 12px; padding: 8px; font-weight: 600; }
QPushButton#AiSumBtn:hover { background: rgba(203,166,247,0.16); border-color: #CBA6F7; }

QMenu#MainMenu { background: #181825; color: #CDD6F4; border: 1px solid #45475A; border-radius: 10px; padding: 6px; }
QMenu#MainMenu::item { padding: 8px 22px; border-radius: 7px; }
QMenu#MainMenu::item:selected { background: #313244; }
QMenu#MainMenu::separator { height: 1px; background: #313244; margin: 5px 8px; }

QScrollBar:vertical { background: #181825; width: 12px; margin: 0; }
QScrollBar::handle:vertical { background: #45475A; border-radius: 6px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #89B4FA; }
QScrollBar:horizontal { background: #181825; height: 12px; margin: 0; }
QScrollBar::handle:horizontal { background: #45475A; border-radius: 6px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background: #89B4FA; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

QSizeGrip { background: transparent; width: 14px; height: 14px; }
QWidget#StatusBar { background: #181825; }
QLabel#StatusText { color: #6C7086; font-size: 11px; }
QToolTip { background: #313244; color: #CDD6F4; border: 1px solid #45475A; border-radius: 6px; padding: 5px 9px; }
QMessageBox { background: #1E1E2E; }
QMessageBox QLabel { color: #CDD6F4; }
QMessageBox QPushButton { background: #313244; color: #CDD6F4; border: 1px solid #45475A;
    border-radius: 9px; padding: 6px 18px; min-width: 70px; }
QMessageBox QPushButton:hover { background: #45475A; }
"""


# ─────────────────────────────────────────────────────────────────────────
#  СПЛЭШ-АНИМАЦИЯ ЗАПУСКА (в стиле Comet)
# ─────────────────────────────────────────────────────────────────────────

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint
                            | Qt.WindowType.WindowStaysOnTopHint
                            | Qt.WindowType.SplashScreen)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(460, 340)
        self._angle = 0.0
        self._progress = 0.0
        try:
            c = QApplication.primaryScreen().geometry().center()
            self.move(c.x() - self.width() // 2, c.y() - self.height() // 2)
        except Exception:
            pass

        self._spin = QVariantAnimation(self)
        self._spin.setStartValue(0.0)
        self._spin.setEndValue(360.0)
        self._spin.setDuration(1050)
        self._spin.setLoopCount(-1)
        self._spin.valueChanged.connect(lambda v: (setattr(self, "_angle", float(v)), self.update()))

        self._prog = QVariantAnimation(self)
        self._prog.setStartValue(0.0)
        self._prog.setEndValue(1.0)
        self._prog.setDuration(1850)
        self._prog.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._prog.valueChanged.connect(lambda v: (setattr(self, "_progress", float(v)), self.update()))

        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self.setWindowOpacity(0.0)

    def start(self):
        self.show()
        self.raise_()
        self._spin.start()
        self._prog.start()
        self._fade.stop()
        self._fade.setDuration(420)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.start()

    def finish(self, win):
        self._spin.stop()
        self._prog.stop()
        self._progress = 1.0
        self.update()
        self._win = win
        self._fade.stop()
        self._fade.setDuration(320)
        self._fade.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade.setStartValue(self.windowOpacity())
        self._fade.setEndValue(0.0)
        # КЛЮЧЕВОЕ: показываем окно в ЧИСТОМ слоте событийного цикла,
        # а не внутри колбэка finished анимации (иначе reentrancy → краш QtCore).
        self._fade.finished.connect(lambda: QTimer.singleShot(0, self._reveal))
        self._fade.start()

    def _reveal(self):
        if self._win is not None:
            self._win.setWindowOpacity(0.0)      # без вспышки: прозрачно → fade-in
            self._win.show()
            self._win.apply_rounded_mask()
            self._win.raise_()
            self._win.activateWindow()
            self._win.play_intro()
        self.close()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(20, 20, -20, -20)

        # карточка с лёгкой обводкой
        p.setPen(QPen(QColor("#313244"), 1))
        p.setBrush(QColor("#181825"))
        p.drawRoundedRect(QRectF(r), 22, 22)

        # логотип (градиент)
        grad = QLinearGradient(float(r.left()), 0.0, float(r.right()), 0.0)
        grad.setColorAt(0.0, QColor("#89B4FA"))
        grad.setColorAt(0.6, QColor("#CBA6F7"))
        grad.setColorAt(1.0, QColor("#A6E3A1"))
        f = QFont("Segoe UI", 34, QFont.Weight.Bold)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 4)
        p.setFont(f)
        p.setPen(QPen(QBrush(grad), 0))
        p.drawText(r.adjusted(0, 64, 0, 0),
                   Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, "PHANTOM")

        # подзаголовок
        p.setFont(QFont("Segoe UI", 10))
        p.setPen(QColor("#6C7086"))
        p.drawText(r.adjusted(0, 122, 0, 0),
                   Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                   "Privacy-first · AI-native browser")

        # спиннер-дуга
        cx, cy, rad = r.center().x(), r.top() + 198, 22
        arc = QRectF(cx - rad, cy - rad, rad * 2, rad * 2)
        p.setPen(QPen(QColor("#313244"), 3))
        p.drawEllipse(arc)
        pen = QPen(QColor("#89B4FA"), 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawArc(arc, int(-self._angle * 16), int(-110 * 16))

        # прогресс-бар
        bar = QRectF(cx - 120, r.bottom() - 36, 240, 5)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#313244"))
        p.drawRoundedRect(bar, 2.5, 2.5)
        p.setBrush(QColor("#89B4FA"))
        p.drawRoundedRect(QRectF(bar.left(), bar.top(), bar.width() * self._progress, bar.height()),
                          2.5, 2.5)
        p.end()


SINGLE_KEY = "PhantomBrowserSingletonV3"


def main():
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setApplicationName("PhantomBrowser")
    app.setOrganizationName("PhantomLabs")
    app.setStyleSheet(QSS)

    # ── ЕДИНСТВЕННЫЙ ЭКЗЕМПЛЯР (как Chrome): второй запуск не плодит копию,
    #    а передаёт URL уже открытому окну. Это и чинит краш «двух копий».
    probe = QLocalSocket()
    probe.connectToServer(SINGLE_KEY)
    if probe.waitForConnected(300):
        arg = sys.argv[1] if len(sys.argv) > 1 else "RAISE"
        probe.write(arg.encode("utf-8"))
        probe.flush()
        probe.waitForBytesWritten(500)
        probe.disconnectFromServer()
        return                       # выходим — окно уже есть
    server = QLocalServer()
    if not server.listen(SINGLE_KEY):
        QLocalServer.removeServer(SINGLE_KEY)   # снять «висячий» сокет после краша
        server.listen(SINGLE_KEY)

    splash = SplashScreen()
    splash.start()
    app.processEvents()          # отрисовать сплэш до тяжёлой инициализации WebEngine

    win = Browser()

    def on_second():
        c = server.nextPendingConnection()
        data = ""
        if c is not None and c.waitForReadyRead(300):
            data = bytes(c.readAll()).decode("utf-8", "ignore").strip()

        def handle():                # отложенно и безопасно — второй запуск не роняет первый
            try:
                if data and data != "RAISE":
                    win.add_tab(data)
                if win.isMinimized():
                    win.showNormal()
                win.raise_()
                win.activateWindow()
            except Exception:
                pass
        QTimer.singleShot(0, handle)
    server.newConnection.connect(on_second)
    win._single_server = server   # держим ссылку, чтобы сервер жил

    QTimer.singleShot(2200, lambda: splash.finish(win))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
