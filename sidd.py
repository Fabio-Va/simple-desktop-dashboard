"""
SiDD - simple-desktop-dashboard
- Calendario sincronizzato con Google Calendar (indirizzo segreto iCal, solo lettura)
- Task con scadenza (compaiono anche nel calendario)
- Sticky notes
- Lanciatore di programmi e link con un click
- S&P 500: ultimi 3 giorni, questo mese, ultimo anno

Tutti i dati restano sul computer, in un file JSON nella cartella dati dell'utente.
"""
import sys
import os
import json
import uuid
import random
import platform
import subprocess
import datetime as dt
from pathlib import Path

import requests

from i18n import _, LANGUAGES, QT_LOCALES, set_language, language
import glass

try:
    from icalendar import Calendar
except ImportError:  # pragma: no cover
    Calendar = None
try:
    import recurring_ical_events
except ImportError:  # pragma: no cover
    recurring_ical_events = None

from PySide6.QtCore import (Qt, QTimer, QDate, QUrl, QObject, Signal, QRunnable, QThreadPool, QPoint,
                            QAbstractNativeEventFilter, QUrlQuery,
                            QStandardPaths, QLocale, QPointF, QRectF, QSize, QFileInfo, QByteArray)
from PySide6.QtGui import (QDesktopServices, QTextCharFormat, QColor, QPainter, QPen, QPainterPath,
                           QFont, QLinearGradient, QBrush, QIcon, QAction, QPixmap, QKeySequence,
                           QShortcut, QGuiApplication, QPalette)
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton,
                               QToolButton, QHBoxLayout, QVBoxLayout, QGridLayout, QCalendarWidget,
                               QListWidget, QListWidgetItem, QLineEdit, QDateEdit, QCheckBox,
                               QPlainTextEdit, QScrollArea, QMenu, QFileDialog, QInputDialog,
                               QMessageBox, QFileIconProvider, QSizePolicy, QToolTip, QTabBar, QKeySequenceEdit, QDialog,
                               QDialogButtonBox, QStackedLayout)

APP_NAME = "SiDD"
APP_VERSION = "1.1.0"
# Aggiornamenti automatici: solo la build ufficiale li riceve. Il file official.py (non su git)
# esiste solo sul PC di chi pubblica le release; chi compila la propria versione modificata non
# riceve aggiornamenti che la sovrascriverebbero, a meno di indicare il proprio repository con
# "update_repo" in config.local.json.
try:
    import official as _official
except ImportError:
    _official = None
UPDATE_REPO = getattr(_official, "UPDATE_REPO", "")
# Segnalazioni bug: indirizzo di un modulo Formspree (o simile). L'email di chi le riceve resta sul
# server del servizio: nel programma e nel traffico c'è solo il codice del modulo.
BUG_REPORT_URL = getattr(_official, "BUG_REPORT_URL", "")
PROJECT_REPO = "Fabio-Va/simple-desktop-dashboard"  # progetto originale (pagina delle segnalazioni)
OLD_APP_NAME = "Dashboard"  # nome precedente: dati e avvio automatico vengono migrati
IT = QLocale(QLocale.Italian, QLocale.Italy)
SYSTEM = platform.system()  # "Windows", "Darwin", "Linux"

# ---------------------------------------------------------------- tema (colori di sistema Apple)
LIGHT = dict(bg="#F2F2F7", surface="#FFFFFF", surface2="#EFEFF4", ink="#1C1C1E", muted="#8A8A8E",
             line="#E3E3E8", accent="#007AFF", accent_ink="#FFFFFF", chip="#DCEBFF", chip_ink="#0057D9",
             up="#248A3D", down="#D70015", board="#FFFFFF")
DARK = dict(bg="#000000", surface="#1C1C1E", surface2="#2C2C2E", ink="#F5F5F7", muted="#98989F",
            line="#2C2C2E", accent="#0A84FF", accent_ink="#FFFFFF", chip="#0A3A70", chip_ink="#CFE4FF",
            up="#30D158", down="#FF453A", board="#1C1C1E")
# vetro smerigliato: colori semi-trasparenti (#AARRGGBB) sopra lo sfondo sfocato di Windows
GLASS = dict(bg="#2E000000", surface="#26FFFFFF", surface2="#1FFFFFFF", ink="#FFFFFF", muted="#B8FFFFFF",
             line="#2EFFFFFF", accent="#0A84FF", accent_ink="#FFFFFF", chip="#660A84FF", chip_ink="#CFE4FF",
             up="#30D158", down="#FF453A", board="#26FFFFFF", flat="transparent", popup="#2C2C2E", glass=True)
for _t in (LIGHT, DARK):
    _t.update(flat=_t["surface"], popup=_t["surface"], glass=False)
NOTE_COLORS = {"giallo": "#FFE27A", "rosa": "#FFC4D3", "menta": "#BFF0D4", "azzurro": "#C7E0FF"}
NOTE_INK = "#26261F"
FONT = '"Segoe UI Variable Text", "Segoe UI", "SF Pro Text", sans-serif'
FONT_DISPLAY = '"Segoe UI Variable Display", "Segoe UI", "SF Pro Display", sans-serif'
DOCK_WIDTH = 0.30  # frazione della larghezza dello schermo
T = LIGHT  # tema attivo, impostato all'avvio


# ---------------------------------------------------------------- squircle
def squircle_path(rect, radius, n=4.0, steps=18):
    """Rettangolo con angoli a superellisse (stile Apple, 'continuous corners')."""
    import math
    r = max(0.0, min(radius, rect.width() / 2, rect.height() / 2))
    path = QPainterPath()
    if r <= 0:
        path.addRect(rect)
        return path
    e = 2.0 / n
    L, Tp, R, B = rect.left(), rect.top(), rect.right(), rect.bottom()
    # (centro dell'angolo, segno x, segno y, verso)
    corners = [((R - r, Tp + r), 1, -1, False), ((R - r, B - r), 1, 1, True),
               ((L + r, B - r), -1, 1, False), ((L + r, Tp + r), -1, -1, True)]
    first = True
    for (cx, cy), sx, sy, forward in corners:
        rng = range(steps + 1) if forward else range(steps, -1, -1)
        for k in rng:
            t = (math.pi / 2) * k / steps
            px = cx + sx * r * (math.cos(t) ** e)
            py = cy + sy * r * (math.sin(t) ** e)
            if first:
                path.moveTo(px, py)
                first = False
            else:
                path.lineTo(px, py)
    path.closeSubpath()
    return path


class Squircle(QFrame):
    """QFrame disegnato come squircle; colori presi dal tema o passati a mano."""

    def __init__(self, radius=26, fill="surface", stroke=None):
        super().__init__()
        self.radius, self.fill, self.stroke = radius, fill, stroke
        self.stroke_w = 1.0

    def _c(self, v):
        return QColor(T.get(v, v)) if isinstance(v, str) else v

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        inset = self.stroke_w / 2 if self.stroke else 0
        path = squircle_path(QRectF(self.rect()).adjusted(inset, inset, -inset, -inset), self.radius)
        p.fillPath(path, self._c(self.fill))
        if self.stroke:
            p.setPen(QPen(self._c(self.stroke), self.stroke_w))
            p.drawPath(path)


def squircle_tile(size, bg, icon=None, letter=None, ink="#FFFFFF"):
    """Icona quadrata con angoli squircle, come quelle di iOS/macOS."""
    dpr = QGuiApplication.primaryScreen().devicePixelRatio() if QGuiApplication.primaryScreen() else 1.0
    pm = QPixmap(int(size * dpr), int(size * dpr))
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    path = squircle_path(QRectF(0, 0, size, size), size * 0.36, n=5)
    p.fillPath(path, QColor(bg))
    if icon is not None:
        s = size * 0.62
        src = icon.pixmap(QSize(int(s * dpr), int(s * dpr)))
        p.drawPixmap(QRectF((size - s) / 2, (size - s) / 2, s, s), src, QRectF(src.rect()))
    elif letter:
        f = QFont()
        f.setPixelSize(int(size * (0.46 if len(letter) == 1 else 0.36)))
        f.setWeight(QFont.DemiBold)
        p.setFont(f)
        p.setPen(QColor(ink))
        p.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, letter)
    p.end()
    return QIcon(pm)


def is_dark():
    try:
        return QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except Exception:
        return QApplication.palette().window().color().lightness() < 128


def stylesheet(t):
    return f"""
    QWidget {{ color:{t['ink']}; font-family:{FONT}; font-size:14px; }}
    QMainWindow, #root {{ background:{t['bg']}; }}
    #h2 {{ font-family:{FONT_DISPLAY}; font-size:18px; font-weight:600; }}
    #h3 {{ font-family:{FONT_DISPLAY}; font-size:15px; font-weight:600; }}
    #greet {{ font-family:{FONT_DISPLAY}; font-size:26px; font-weight:700; }}
    #clock {{ font-family:{FONT_DISPLAY}; font-size:40px; font-weight:600; }}
    #muted, #status {{ color:{t['muted']}; }}
    #status {{ font-size:12px; }}
    #price {{ font-family:{FONT_DISPLAY}; font-size:28px; font-weight:700; }}
    #msg {{ background:{t['surface2']}; border-radius:12px; padding:9px 12px; color:{t['muted']}; }}
    QPushButton, QToolButton#btn {{ background:{t['surface2']}; color:{t['accent']}; border:none;
        border-radius:14px; padding:5px 13px; min-height:18px; font-weight:600; }}
    QPushButton:hover, QToolButton#btn:hover {{ background:{t['line']}; }}
    QPushButton#primary {{ background:{t['accent']}; color:{t['accent_ink']}; }}
    QPushButton#primary:hover {{ background:{t['chip_ink']}; }}
    QToolButton#btn::menu-indicator {{ image:none; width:0; }}
    QToolButton#round {{ background:{t['surface']}; color:{t['muted']}; border:none; border-radius:15px;
        min-width:30px; max-width:30px; min-height:30px; max-height:30px; font-size:14px; }}
    QToolButton#round:hover {{ background:{t['surface2']}; color:{t['ink']}; }}
    QToolButton#round::menu-indicator {{ image:none; width:0; }}
    QToolButton#app {{ background:transparent; border:none; border-radius:14px; padding:4px 2px;
        color:{t['ink']}; font-size:12px; }}
    QToolButton#app:hover {{ background:{t['surface2']}; }}
    QLineEdit, QDateEdit {{ background:{t['surface2']}; border:1.5px solid transparent;
        border-radius:11px; padding:7px 10px; }}
    QLineEdit:focus, QDateEdit:focus {{ border-color:{t['accent']}; }}
    QDateEdit::drop-down {{ border:none; width:22px; }}
    QListWidget {{ background:transparent; border:none; outline:none; }}
    QListWidget::item {{ padding:5px 6px; border-radius:10px; }}
    QListWidget::item:hover {{ background:{t['surface2']}; }}
    QListWidget::item:selected {{ background:{t['chip']}; color:{t['ink']}; }}
    QListWidget::indicator, QCheckBox::indicator {{ width:16px; height:16px; border:1.5px solid {t['muted']};
        border-radius:9px; background:transparent; }}
    QListWidget::indicator:checked, QCheckBox::indicator:checked {{ background:{t['accent']}; border-color:{t['accent']}; }}
    QCalendarWidget QWidget#qt_calendar_navigationbar {{ background:{t['flat']}; }}
    QCalendarWidget QToolButton {{ color:{t['ink']}; background:transparent; font-size:13px; font-weight:600;
        padding:2px 4px; border-radius:8px; }}
    QCalendarWidget QToolButton:hover {{ background:{t['surface2']}; }}
    QCalendarWidget QToolButton::menu-indicator {{ image:none; width:0; }}
    QCalendarWidget QSpinBox {{ font-size:13px; font-weight:600; background:{t['surface2']}; border:none;
        border-radius:6px; padding:1px 2px; }}
    QCalendarWidget QAbstractItemView {{ background:{t['flat']}; selection-background-color:transparent;
        selection-color:{t['ink']}; outline:none; border:none; }}
    QCheckBox {{ spacing:8px; }}
    QPushButton#seg {{ background:{t['surface2']}; color:{t['ink']}; font-weight:500; }}
    QPushButton#seg:checked {{ background:{t['accent']}; color:{t['accent_ink']}; }}
    QToolButton#round:checked {{ background:{t['accent']}; color:{t['accent_ink']}; }}
    QTabBar#tabs {{ background:transparent; border:none; border-bottom:1px solid {t['line']}; }}
    QTabBar#tabs::tab {{ background:transparent; color:{t['muted']}; border:none; padding:6px 12px;
        margin-right:2px; border-top-left-radius:10px; border-top-right-radius:10px; font-size:13px;
        font-weight:600; min-width:40px; }}
    QTabBar#tabs::tab:hover {{ background:{t['surface2']}; color:{t['ink']}; }}
    QTabBar#tabs::tab:selected {{ background:{t['surface2']}; color:{t['ink']};
        border-bottom:2px solid {t['accent']}; }}
    QTabBar QToolButton {{ background:{t['surface']}; border:none; border-radius:8px; color:{t['ink']}; }}
    QScrollArea {{ background:transparent; border:none; }}
    QScrollArea > QWidget > QWidget {{ background:transparent; }}
    QScrollArea > QWidget > QWidget#overlay {{ background:{'#F5141416' if t.get('glass') else t['bg']}; }}
    QScrollBar:vertical {{ background:transparent; width:8px; margin:4px 1px; }}
    QScrollBar::handle:vertical {{ background:{t['muted']}; border-radius:3px; min-height:40px; }}
    QScrollBar::handle:vertical:!hover {{ background:{t['line']}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height:0; width:0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background:none; }}
    QMenu {{ background:{t['popup']}; border:1px solid {t['line']}; padding:5px; }}
    QMenu::item {{ padding:7px 20px; border-radius:8px; }}
    QMenu::item:selected {{ background:{t['chip']}; color:{t['ink']}; }}
    QMenu::separator {{ height:1px; background:{t['line']}; margin:4px 8px; }}
    QDialog, QMessageBox, QInputDialog {{ background:{t['popup']}; }}
    QPlainTextEdit#bugtext {{ background:{t['surface2']}; border:1.5px solid transparent; border-radius:11px;
        padding:6px 8px; }}
    QPlainTextEdit#bugtext:focus {{ border-color:{t['accent']}; }}
    QKeySequenceEdit QLineEdit {{ padding:5px 8px; }}
    QToolTip {{ background:{t['popup']}; color:{t['ink']}; border:1px solid {t['line']}; padding:4px 6px; }}
    """


def it_num(v, dec=2):
    """Numero formattato secondo la lingua scelta (1.234,56 / 1,234.56 / 1 234,56)."""
    return IT.toString(float(v), "f", dec)


def apply_language(store):
    """Imposta lingua dei testi e formato di date/numeri."""
    global IT
    set_language(store.data.get("lang", "it"))
    IT = QLocale(QT_LOCALES[language()])
    QLocale.setDefault(IT)


def it_short(dstr):
    d = QDate.fromString(dstr, "yyyy-MM-dd")
    return IT.toString(d, "d MMM")


# ---------------------------------------------------------------- dati
class Store:
    DEFAULTS = {"ical_urls": [], "tasks": [], "notes": [], "apps": [],
                "on_bottom": False, "side": "right", "theme": "dark", "hidden": [],
                "presets": {}, "music": "", "collapsed": [], "lang": "it", "markets": ["spx"],
                "custom_markets": [], "weather_loc": None, "hotkey": "Ctrl+Alt+D"}
    # impostazioni (ripristinabili); il resto sono i tuoi contenuti: note, task, app, calendari,
    # località del meteo e titoli personalizzati
    SETTINGS = ("on_bottom", "side", "theme", "hidden", "presets", "music", "collapsed", "lang", "markets",
                "hotkey")

    def __init__(self):
        base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        self.dir = Path(base)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / "data.json"
        old = self.dir.parent / OLD_APP_NAME / "data.json"
        if not self.path.exists() and self.dir.name == APP_NAME and old.exists():
            try:  # prima installazione col nuovo nome: riprendo i dati della vecchia "Dashboard"
                self.path.write_bytes(old.read_bytes())
            except OSError:
                pass
        self.data = json.loads(json.dumps(self.DEFAULTS))
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    self.data.update(loaded)
            except Exception:
                backup = self.path.with_suffix(".corrotto.json")
                try:
                    self.path.replace(backup)
                except OSError:
                    pass
        self._timer = QTimer(singleShot=True, interval=600)
        self._timer.timeout.connect(self.save_now)

    def save(self):
        self._timer.start()

    def save_now(self):
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)


# ---------------------------------------------------------------- lavori in background
class WorkerSignals(QObject):
    done = Signal(object)
    failed = Signal(str)


class Worker(QRunnable):
    def __init__(self, fn, *args):
        super().__init__()
        self.fn, self.args = fn, args
        self.signals = WorkerSignals()

    def run(self):
        try:
            try:
                result = self.fn(*self.args)
            except Exception as e:  # noqa: BLE001
                self.signals.failed.emit(str(e) or e.__class__.__name__)
            else:
                self.signals.done.emit(result)
        except RuntimeError:  # il programma si è chiuso mentre scaricava
            pass


_alive = set()


def run_bg(fn, args, on_done, on_fail):
    w = Worker(fn, *args)
    _alive.add(w)
    w.setAutoDelete(False)
    def safe(fn, v):
        _alive.discard(w)
        try:
            fn(v)
        except RuntimeError:  # il pannello è stato ricostruito (cambio tema) nel frattempo
            pass
    w.signals.done.connect(lambda r: safe(on_done, r))
    w.signals.failed.connect(lambda m: safe(on_fail, m))
    QThreadPool.globalInstance().start(w)


# ---------------------------------------------------------------- calendario (iCal)
def _to_local(x):
    if isinstance(x, dt.datetime):
        return x.astimezone() if x.tzinfo else x
    return x


def fetch_calendar(urls):
    if Calendar is None:
        raise RuntimeError("Manca il pacchetto icalendar")
    today = dt.date.today()
    start, end = today - dt.timedelta(days=62), today + dt.timedelta(days=200)
    days, errors, ok = {}, [], 0
    for raw in urls:
        u = raw.strip()
        if not u:
            continue
        if u.lower().startswith("webcal://"):
            u = "https://" + u[9:]
        try:
            if os.path.exists(u):
                content = Path(u).read_bytes()
            else:
                r = requests.get(u, timeout=25, headers={"User-Agent": "SiDD/1.0"})
                r.raise_for_status()
                content = r.content
            cal = Calendar.from_ical(content)
        except Exception as e:  # noqa: BLE001
            errors.append(str(e))
            continue
        ok += 1
        cal_name = str(cal.get("X-WR-CALNAME", "") or "")
        if recurring_ical_events is not None:
            comps = recurring_ical_events.of(cal).between(start, end)
        else:
            comps = list(cal.walk("VEVENT"))
        for ev in comps:
            if str(ev.get("STATUS", "")).upper() == "CANCELLED":
                continue
            ds = ev.get("DTSTART")
            if ds is None:
                continue
            s = _to_local(ds.dt)
            de = ev.get("DTEND")
            e = _to_local(de.dt) if de is not None else None
            title = str(ev.get("SUMMARY", "") or _("(senza titolo)"))
            if isinstance(s, dt.datetime):
                if not isinstance(e, dt.datetime) or e < s:
                    e = s
                first = s.date()
                last = (e - dt.timedelta(seconds=1)).date() if e > s else first
                label = s.strftime("%H:%M") + ("–" + e.strftime("%H:%M") if e > s else "")
                d = first
                while d <= last and (d - first).days < 31:
                    if start <= d <= end:
                        days.setdefault(d.isoformat(), []).append(
                            {"title": title, "time": label, "sort": s.strftime("%H:%M"), "cal": cal_name})
                    d += dt.timedelta(days=1)
            else:
                if not isinstance(e, dt.date) or e <= s:
                    e = s + dt.timedelta(days=1)
                d = s
                while d < e and (d - s).days < 31:
                    if start <= d <= end:
                        days.setdefault(d.isoformat(), []).append(
                            {"title": title, "time": "tutto il giorno", "sort": "00:00", "cal": cal_name})
                    d += dt.timedelta(days=1)
    if ok == 0 and errors:
        raise RuntimeError(errors[0])
    for lst in days.values():
        lst.sort(key=lambda x: (x["time"] != "tutto il giorno", x["sort"]))
    return {"days": days, "errors": errors, "fetched": dt.datetime.now().strftime("%H:%M")}


# ---------------------------------------------------------------- mercati
# chiave -> nome, simbolo Yahoo Finance, simbolo Stooq (riserva), unità
MARKETS = {
    "spx": ("S&P 500", "^GSPC", "^spx", "punti"),
    "ndx": ("Nasdaq 100", "^NDX", "^ndx", "punti"),
    "dji": ("Dow Jones", "^DJI", "^dji", "punti"),
    "ftsemib": ("FTSE MIB", "FTSEMIB.MI", None, "punti"),
    "btc": ("Bitcoin", "BTC-USD", "btcusd", "USD"),
    "gold": ("Oro", "GC=F", "xauusd", "USD/oz"),
}
DEFAULT_MARKETS = ["spx"]


def sync_custom_markets(store):
    """Aggiunge a MARKETS i titoli personalizzati (chiave "c:SIMBOLO", unità = valuta di Yahoo)."""
    for k in [k for k in MARKETS if k.startswith("c:")]:
        del MARKETS[k]
    for c in store.data.get("custom_markets", []):
        if isinstance(c, dict) and c.get("symbol"):
            MARKETS["c:" + c["symbol"]] = (c.get("name") or c["symbol"], c["symbol"], None, None)


def _yahoo(symbol):
    r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/" + requests.utils.quote(symbol, safe=""),
                     params={"range": "1y", "interval": "1d"},
                     headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    closes = res["indicators"]["quote"][0]["close"]
    pts = [(dt.datetime.fromtimestamp(t, dt.timezone.utc).date().isoformat(), float(c))
           for t, c in zip(res["timestamp"], closes) if c is not None]
    meta = res.get("meta", {})
    price = meta.get("regularMarketPrice")
    if price and pts:
        pts[-1] = (pts[-1][0], float(price))
    return pts, "Yahoo Finance", meta.get("currency") or ""


def _stooq(symbol):
    r = requests.get("https://stooq.com/q/d/l/", params={"s": symbol, "i": "d"},
                     headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    r.raise_for_status()
    lines = r.text.strip().splitlines()
    if not lines or not lines[0].lower().startswith("date"):
        raise RuntimeError("risposta Stooq non valida")
    cutoff = (dt.date.today() - dt.timedelta(days=380)).isoformat()
    pts = []
    for ln in lines[1:]:
        p = ln.split(",")
        if len(p) >= 5 and p[0] >= cutoff:
            pts.append((p[0], float(p[4])))
    return pts, "Stooq", ""


def fetch_market(key):
    _name, ysym, ssym, _unit = MARKETS[key]
    errs = []
    for fn, sym in ((_yahoo, ysym), (_stooq, ssym)):
        if not sym:
            continue
        try:
            pts, src, currency = fn(sym)
            if len(pts) >= 5:
                return {"points": pts, "source": src, "currency": currency,
                        "fetched": dt.datetime.now().strftime("%H:%M")}
            errs.append(f"{src}: pochi dati")
        except Exception as e:  # noqa: BLE001
            errs.append(str(e))
    raise RuntimeError("; ".join(errs))


def fetch_markets(keys):
    """Scarica tutti i titoli scelti; per ognuno il risultato o il messaggio d'errore."""
    out = {}
    for k in keys:
        try:
            out[k] = fetch_market(k)
        except Exception as e:  # noqa: BLE001
            out[k] = {"error": str(e)}
    return out


def range_points(pts, key):
    if len(pts) < 2:
        return []
    last = pts[-1]
    if key == "d3":
        return pts[-4:]
    if key == "mtd":
        ym = last[0][:7]
        idx = next((i for i, p in enumerate(pts) if p[0][:7] == ym), len(pts) - 1)
        return pts[max(0, idx - 1):]
    cutoff = (dt.date.fromisoformat(last[0]) - dt.timedelta(days=365)).isoformat()
    idx = next((i for i, p in enumerate(pts) if p[0] >= cutoff), 0)
    return pts[max(0, idx - 1):]


# ---------------------------------------------------------------- meteo (Open-Meteo, gratuito e senza chiave)
# codice meteo WMO -> (emoji di giorno, emoji di notte, descrizione)
WMO = [((0,), "☀️", "🌙", "Sereno"), ((1,), "🌤️", "🌙", "Poco nuvoloso"), ((2,), "⛅", "☁️", "Parzialmente nuvoloso"),
       ((3,), "☁️", "☁️", "Coperto"), ((45, 48), "🌫️", "🌫️", "Nebbia"), ((51, 53, 55, 56, 57), "🌦️", "🌧️", "Pioggerella"),
       ((61, 63, 65, 66, 67), "🌧️", "🌧️", "Pioggia"), ((71, 73, 75, 77), "🌨️", "🌨️", "Neve"),
       ((80, 81, 82), "🌦️", "🌧️", "Rovesci"), ((85, 86), "🌨️", "🌨️", "Rovesci di neve"),
       ((95, 96, 99), "⛈️", "⛈️", "Temporale")]


def wmo(code, day=True):
    for codes, d, n, text in WMO:
        if code in codes:
            return (d if day else n), text
    return "🌡️", ""


def geocode(name):
    """Cerca una località per nome: lista di {"name", "lat", "lon", "label"}."""
    r = requests.get("https://geocoding-api.open-meteo.com/v1/search",
                     params={"name": name, "count": 8, "language": language(), "format": "json"},
                     headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}"}, timeout=20)
    r.raise_for_status()
    out = []
    for x in r.json().get("results", []) or []:
        parts = [x.get("name"), x.get("admin1"), x.get("country")]
        label = ", ".join(dict.fromkeys(p for p in parts if p))
        out.append({"name": x.get("name", name), "lat": x["latitude"], "lon": x["longitude"], "label": label})
    return out


def fetch_weather(lat, lon):
    r = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": lat, "longitude": lon, "timezone": "auto", "forecast_days": 6,
        "current": "temperature_2m,apparent_temperature,weather_code,is_day,wind_speed_10m,relative_humidity_2m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"},
        headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}"}, timeout=20)
    r.raise_for_status()
    j = r.json()
    j["fetched"] = dt.datetime.now().strftime("%H:%M")
    return j


# ---------------------------------------------------------------- aggiornamenti (release GitHub)
def version_tuple(v):
    parts = []
    for x in str(v).lstrip("vV").split("."):
        num = "".join(ch for ch in x if ch.isdigit())
        parts.append(int(num) if num else 0)
    return tuple(parts + [0] * (3 - len(parts)))


def update_repo():
    """Repository GitHub da cui arrivano gli aggiornamenti ("" = aggiornamenti disattivati)."""
    return str(LOCAL.get("update_repo") or UPDATE_REPO).strip()


def fetch_latest_release():
    """Ultima release pubblicata: versione, pagina e indirizzo di SiDD.exe."""
    repo = update_repo()
    if not repo:
        return None
    r = requests.get(f"https://api.github.com/repos/{repo}/releases/latest",
                     headers={"Accept": "application/vnd.github+json", "User-Agent": f"{APP_NAME}/{APP_VERSION}"},
                     timeout=20)
    if r.status_code == 404:
        return None  # nessuna release (o repository non pubblico)
    r.raise_for_status()
    j = r.json()
    exe = next((a for a in j.get("assets", []) if a.get("name", "").lower() == "sidd.exe"), None)
    return {"version": j.get("tag_name", "").lstrip("vV"), "page": j.get("html_url", ""),
            "notes": j.get("body") or "",
            "url": exe["browser_download_url"] if exe else None, "size": exe.get("size", 0) if exe else 0}


def download_update(url, size):
    """Scarica la nuova versione accanto all'exe attuale (SiDD.exe.new)."""
    dest = Path(sys.executable).with_suffix(".exe.new")
    with requests.get(url, stream=True, timeout=60, headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}"}) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)
    got = dest.stat().st_size
    if got < 1_000_000 or (size and got != size):
        dest.unlink(missing_ok=True)
        raise RuntimeError(_("Download incompleto."))
    return str(dest)


def install_update(new_path):
    """Sostituisce l'exe appena il programma si chiude e lo riapre (script temporaneo)."""
    exe = sys.executable
    script = Path(os.environ.get("TEMP", str(Path(exe).parent))) / "sidd-update.cmd"
    script.write_text(
        "@echo off\r\n"
        "set n=0\r\n"
        ":retry\r\n"
        "timeout /t 1 /nobreak >nul\r\n"
        f'move /y "{new_path}" "{exe}" >nul 2>nul && goto ok\r\n'
        "set /a n+=1\r\n"
        "if %n% lss 30 goto retry\r\n"
        "goto end\r\n"
        ":ok\r\n"
        f'start "" "{exe}"\r\n'
        ":end\r\n"
        'del "%~f0"\r\n', encoding="mbcs" if SYSTEM == "Windows" else "utf-8", errors="replace")
    subprocess.Popen(["cmd", "/c", str(script)], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
                     | getattr(subprocess, "DETACHED_PROCESS", 0), close_fds=True)


# ---------------------------------------------------------------- scorciatoia globale (Windows)
HOTKEY_ID = 0x51DD
WM_HOTKEY = 0x0312


def _vk(key):
    """Tasto Qt -> codice virtuale Windows (lettere, numeri, F1–F24, spazio e pochi altri)."""
    k = int(getattr(key, "value", key))
    if 0x41 <= k <= 0x5A or 0x30 <= k <= 0x39:
        return k
    if Qt.Key_F1.value <= k <= Qt.Key_F24.value:
        return 0x70 + k - Qt.Key_F1.value
    return {Qt.Key_Space.value: 0x20, Qt.Key_Home.value: 0x24, Qt.Key_End.value: 0x23,
            Qt.Key_Insert.value: 0x2D, Qt.Key_PageUp.value: 0x21, Qt.Key_PageDown.value: 0x22,
            Qt.Key_Pause.value: 0x13}.get(k)


def set_global_hotkey(text):
    """Registra la combinazione (es. "Ctrl+Alt+D"); "" la toglie. False se non è possibile."""
    if SYSTEM != "Windows":
        return not text
    import ctypes
    user32 = ctypes.windll.user32
    user32.UnregisterHotKey(None, HOTKEY_ID)
    if not text:
        return True
    seq = QKeySequence(text, QKeySequence.PortableText)
    if seq.isEmpty():
        return False
    comb = seq[0]
    mods, flags = comb.keyboardModifiers(), 0x4000  # MOD_NOREPEAT
    for qt_mod, win_mod in ((Qt.AltModifier, 1), (Qt.ControlModifier, 2), (Qt.ShiftModifier, 4),
                            (Qt.MetaModifier, 8)):
        if mods & qt_mod:
            flags |= win_mod
    vk = _vk(comb.key())
    if vk is None or not (flags & 0xB):  # serve almeno Ctrl, Alt o Win
        return False
    return bool(user32.RegisterHotKey(None, HOTKEY_ID, flags, vk))


def toggle_window():
    if not _windows:
        return
    w = _windows[-1]
    if w.isVisible() and not w.isMinimized():
        w.hide()
    else:
        w.showNormal()
        w.dock_to_screen()
        w.raise_()
        w.activateWindow()


class HotkeyFilter(QAbstractNativeEventFilter):
    """Riceve da Windows il messaggio della scorciatoia globale."""

    def nativeEventFilter(self, etype, message):
        if bytes(etype) == b"windows_generic_MSG":
            from ctypes import wintypes
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                QTimer.singleShot(0, toggle_window)
                return True, 0
        return False, 0


# ---------------------------------------------------------------- segnalazione bug
def system_info():
    return f"{APP_NAME} {APP_VERSION} · {platform.platform()} · Python {platform.python_version()}"


def send_bug_report(text, contact, info):
    """Invia la segnalazione al modulo configurato. Restituisce True se è partita."""
    payload = {"_subject": f"{APP_NAME} – bug report", "message": text,
               "version": APP_VERSION, "system": info or ""}
    if contact:
        payload["email"] = contact  # risposta a chi ha segnalato, se l'ha indicata
    r = requests.post(BUG_REPORT_URL, json=payload, timeout=20,
                      headers={"Accept": "application/json", "User-Agent": f"{APP_NAME}/{APP_VERSION}"})
    r.raise_for_status()
    return True


def github_issue_url(text, info):
    q = QUrlQuery()
    q.addQueryItem("title", "Bug: " + text.strip().splitlines()[0][:80] if text.strip() else "Bug")
    q.addQueryItem("body", text + ("\n\n---\n" + info if info else ""))
    u = QUrl(f"https://github.com/{update_repo() or PROJECT_REPO}/issues/new")
    u.setQuery(q)
    return u.toString(QUrl.FullyEncoded)


class BugDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(_("Segnala un bug"))
        self.setMinimumWidth(420)
        lay = QVBoxLayout(self)
        lay.setSpacing(8)
        lay.addWidget(label(_("Cosa non funziona? Descrivi cosa stavi facendo e cosa è successo."), wrap=True))
        self.text = QPlainTextEdit()
        self.text.setObjectName("bugtext")
        self.text.setMinimumHeight(150)
        lay.addWidget(self.text)
        self.contact = QLineEdit()
        self.contact.setPlaceholderText(_("La tua email (facoltativa, per poterti rispondere)"))
        lay.addWidget(self.contact)
        self.info = QCheckBox(_("Includi versione e sistema operativo"))
        self.info.setChecked(True)
        self.info.setToolTip(system_info())
        lay.addWidget(self.info)
        note = (_("La segnalazione arriva direttamente allo sviluppatore.") if BUG_REPORT_URL else
                _("Si apre la pagina delle segnalazioni su GitHub (serve un account GitHub)."))
        lay.addWidget(label(note, "status", wrap=True))
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText(_("Invia"))
        bb.button(QDialogButtonBox.Ok).setObjectName("primary")
        bb.button(QDialogButtonBox.Cancel).setText(_("Annulla"))
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)


# ---------------------------------------------------------------- utilità UI
def label(text="", name=None, wrap=False):
    lb = QLabel(text)
    if name:
        lb.setObjectName(name)
    lb.setWordWrap(wrap)
    return lb


class Panel(Squircle):
    """Scheda bianca con angoli squircle, titolo, riga di stato e pulsanti a destra."""

    collapsedChanged = Signal(bool)

    def __init__(self, title, name="panel", compact=False):
        super().__init__(radius=26 if compact else 30, fill="surface")
        self.setObjectName(name)
        sp = 8 if compact else 10
        self.outer = QVBoxLayout(self)
        if compact:
            self.outer.setContentsMargins(12, 12, 12, 12)
        else:
            self.outer.setContentsMargins(18, 14, 18, 18)
        self.outer.setSpacing(sp)
        self.head = QHBoxLayout()
        self.head.setSpacing(4 if compact else 6)
        titles = QVBoxLayout()
        titles.setSpacing(0)
        self.title = label(title, "h3" if compact else "h2")
        self.title.setVisible(bool(title))
        titles.addWidget(self.title)
        self.status = label("", "status")
        self.status.hide()
        titles.addWidget(self.status)
        self.head.addLayout(titles)
        self.head.addStretch(1)
        self.outer.addLayout(self.head)
        # contenuto della scheda: si nasconde quando la scheda è ridotta
        self.body = QWidget()
        self.lay = QVBoxLayout(self.body)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(sp)
        self.outer.addWidget(self.body, 1)
        self.collapsed = False
        self.chevron = None
        if T.get("glass"):
            glass.Light.get().register(self)

    def paintEvent(self, ev):
        if not T.get("glass"):
            return super().paintEvent(ev)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = squircle_path(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), self.radius)
        glass.paint_glass(self, p, path)

    def set_status(self, text):
        self.status.setText(text)
        self.status.setVisible(bool(text))

    def enable_collapse(self, store, key):
        """Aggiunge in alto a destra il pulsante per ridurre/espandere la scheda."""
        self.store, self.collapse_key = store, key
        self.chevron = ChevronButton()
        self.chevron.clicked.connect(lambda: self.set_collapsed(not self.collapsed))
        self.head.addWidget(self.chevron)
        self.set_collapsed(key in store.data.get("collapsed", []), save=False)

    def set_collapsed(self, on, save=True):
        self.collapsed = on
        self.body.setVisible(not on)
        for i in range(self.head.count()):  # nasconde i pulsanti d'azione, non il titolo
            w = self.head.itemAt(i).widget()
            if w is not None and w is not self.chevron:
                w.setVisible(not on)
        m = self.outer.contentsMargins()
        self.outer.setContentsMargins(m.left(), m.top(), m.right(),
                                      m.top() if on else (12 if self.radius == 26 else 18))
        self.chevron.set_up(not on)
        self.chevron.setToolTip(_("Espandi") if on else _("Riduci"))
        if save:
            lst = [k for k in self.store.data.get("collapsed", []) if k != self.collapse_key]
            if on:
                lst.append(self.collapse_key)
            self.store.data["collapsed"] = lst
            self.store.save()
        self.collapsedChanged.emit(on)


class ChevronButton(QToolButton):
    """Pulsantino rotondo con una freccetta disegnata (su = riduci, giù = espandi)."""

    def __init__(self):
        super().__init__()
        self.up = True
        self.setFixedSize(26, 26)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("QToolButton{background:transparent;border:none;}")

    def set_up(self, up):
        self.up = up
        self.update()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        bg = QColor(T["line"] if self.underMouse() else T["surface2"])
        p.setPen(Qt.NoPen)
        p.setBrush(bg)
        p.drawEllipse(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5))
        c = QRectF(self.rect()).center()
        dy = -2.0 if self.up else 2.0
        path = QPainterPath(QPointF(c.x() - 4.5, c.y() - dy))
        path.lineTo(QPointF(c.x(), c.y() + dy))
        path.lineTo(QPointF(c.x() + 4.5, c.y() - dy))
        p.setPen(QPen(QColor(T["muted"]), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)

    def enterEvent(self, e):
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.update()
        super().leaveEvent(e)


class ResponsiveGrid(QWidget):
    """Griglia che sceglie da sola il numero di colonne in base alla larghezza."""

    def __init__(self, min_item_w, spacing=10, item_h=None):
        super().__init__()
        self.min_w, self.sp, self.item_h = min_item_w, spacing, item_h
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(spacing)
        self.items = []
        self._cols = 0
        self.align_right = False

    def set_align_right(self, on):
        if on != self.align_right:
            self.align_right = on
            self._cols = 0
            self.relayout()

    def set_items(self, widgets):
        for w in self.items:
            w.setParent(None)
            w.deleteLater()
        self.items = list(widgets)
        self._cols = 0
        self.relayout()

    def relayout(self):
        w = max(1, self.width())
        cols = max(1, (w + self.sp) // (self.min_w + self.sp))
        if cols == self._cols and self.grid.count() == len(self.items):
            return
        self._cols = cols
        while self.grid.count():
            self.grid.takeAt(0)
        for c in range(max(cols, self.grid.columnCount())):
            self.grid.setColumnStretch(c, 1 if c < cols else 0)
            self.grid.setColumnMinimumWidth(c, 0)
        n = len(self.items)
        for i, it in enumerate(self.items):
            it.setMinimumWidth(0)
            it.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            if self.item_h:
                it.setFixedHeight(self.item_h)
            row, c = divmod(i, cols)
            if self.align_right:
                in_row = min(cols, n - row * cols)  # l'ultima riga può essere incompleta
                c += cols - in_row
            self.grid.addWidget(it, row, c)
        self.updateGeometry()

    def minimumSizeHint(self):
        return QSize(self.min_w, super().minimumSizeHint().height())

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.relayout()


def fit_list(lw, min_h=40):
    """Rende una lista alta quanto il suo contenuto (scorre la colonna intera, non la lista)."""
    ls = lw.fontMetrics().lineSpacing()
    for i in range(lw.count()):
        it = lw.item(i)
        it.setSizeHint(QSize(-1, ls * (it.text().count("\n") + 1) + 6))
    lw.doItemsLayout()
    h = sum(lw.sizeHintForRow(i) for i in range(lw.count())) + 2 * lw.frameWidth() + 6
    lw.setFixedHeight(max(min_h, h))


class AutoList(QListWidget):
    """Lista senza barra di scorrimento che si adatta all'altezza del contenuto."""

    def __init__(self):
        super().__init__()
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWordWrap(False)
        self.setTextElideMode(Qt.ElideRight)
        self._w = -1

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if e.size().width() != self._w:
            self._w = e.size().width()
            QTimer.singleShot(0, lambda: fit_list(self))

    def wheelEvent(self, e):
        e.ignore()  # lascia scorrere la colonna


def small_button(text, tip, fn, name=None):
    b = QPushButton(text)
    if name:
        b.setObjectName(name)
    b.setToolTip(tip)
    b.setCursor(Qt.PointingHandCursor)
    b.clicked.connect(fn)
    return b


def open_url(u):
    QDesktopServices.openUrl(QUrl(u))


def gcal_template(text="", day=None):
    from urllib.parse import urlencode
    p = {"action": "TEMPLATE"}
    if text:
        p["text"] = text
    if day:
        d = dt.date.fromisoformat(day)
        p["dates"] = d.strftime("%Y%m%d") + "/" + (d + dt.timedelta(days=1)).strftime("%Y%m%d")
    return "https://calendar.google.com/calendar/render?" + urlencode(p)


# ---------------------------------------------------------------- lanciatore
ICON_BG = ["#007AFF", "#FF9500", "#34C759", "#AF52DE", "#FF2D55", "#32ADE6", "#5856D6", "#FF3B30"]
TILE = 52


def is_link(target):
    t = target.strip().lower()
    return "://" in t or t.startswith(("mailto:", "spotify:", "steam:", "ms-")) and not os.path.exists(target)


def launch(target, args=None):
    if args:
        subprocess.Popen([os.path.expandvars(target)] + list(args), cwd=os.path.dirname(target) or None,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return
    if target.lower().startswith("shell:") and SYSTEM == "Windows":
        os.startfile(target)  # noqa: S606  (app dello Store, es. iTunes)
        return
    if is_link(target):
        open_url(target)
        return
    path = os.path.expanduser(target)
    if not os.path.exists(path):
        raise FileNotFoundError(_("Non trovo «{path}»", path=path))
    if SYSTEM == "Windows":
        os.startfile(path)  # noqa: S606
    elif SYSTEM == "Darwin":
        subprocess.Popen(["open", path])
    else:
        if path.endswith(".desktop"):
            subprocess.Popen(["gio", "launch", path]) if _which("gio") else subprocess.Popen(["xdg-open", path])
        elif os.access(path, os.X_OK) and os.path.isfile(path):
            subprocess.Popen([path], start_new_session=True, cwd=os.path.dirname(path) or None)
        else:
            subprocess.Popen(["xdg-open", path])


# ---- app predefinite, attivabili dalle impostazioni
def app_dir():
    """Cartella del programma (accanto a SiDD.exe o a sidd.py)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def load_local_config():
    """config.local.json (facoltativo, non va su git): app personali e percorsi di questo PC.
    Vedi config.example.json."""
    p = app_dir() / "config.local.json"
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except (OSError, ValueError):
        return {}


LOCAL = load_local_config()

PRESETS = {
    "epicpen": {"name": "Epic Pen", "color": "#FF2D55", "glyph": "✎",
                "candidates": [r"%ProgramFiles(x86)%\Epic Pen\EpicPen.exe", r"%ProgramFiles%\Epic Pen\EpicPen.exe",
                               r"%LOCALAPPDATA%\Programs\Epic Pen\EpicPen.exe"]},
    "screenshot": {"name": "Screenshot", "color": "#5856D6", "glyph": "✂", "candidates": ["ms-screenclip:"]},
}
PRESET_DEFAULTS = {"epicpen": False, "screenshot": False}
# app personali dal config locale (vedi config.example.json):
#   {"chiave": {"name", "color", "glyph", "ink", "path" | "choices": [{"label", "path", "args", "check"}]}}
# con "choices" il pulsante apre un fumetto con più scelte (es. più versioni dello stesso programma)
for _k, _p in LOCAL.get("presets", {}).items():
    if not (isinstance(_p, dict) and _p.get("name")):
        continue
    _d = {"name": _p["name"], "color": _p.get("color", "#8E8E93"), "ink": _p.get("ink", "#FFFFFF"),
          "glyph": _p.get("glyph", _p["name"][:1].upper()), "tip": _p.get("tip", "")}
    if isinstance(_p.get("choices"), list) and _p["choices"]:
        _d["choices"] = [c for c in _p["choices"] if isinstance(c, dict) and c.get("path")]
    elif _p.get("path"):
        _d["candidates"] = [_p["path"]]
    else:
        continue
    PRESETS[_k] = _d
    PRESET_DEFAULTS.setdefault(_k, True)
PRESET_DEFAULTS.update({k: bool(v) for k, v in LOCAL.get("preset_defaults", {}).items()})
MUSIC = {
    "vlc": {"name": "VLC", "color": "#FF8800", "glyph": "▶",
            "candidates": [r"%ProgramFiles%\VideoLAN\VLC\vlc.exe", r"%ProgramFiles(x86)%\VideoLAN\VLC\vlc.exe"]},
    "itunes": {"name": "iTunes", "color": "#FA2D48", "glyph": "♪",
               "candidates": [r"%ProgramFiles%\iTunes\iTunes.exe",
                              r"shell:AppsFolder\AppleInc.iTunes_nzyj5cx40ttqa!iTunes"]},
    "spotify": {"name": "Spotify", "color": "#1DB954", "glyph": "♫",
                "candidates": [r"%APPDATA%\Spotify\Spotify.exe", "spotify:"]},
}


def resolve_target(candidates):
    """Primo percorso esistente; altrimenti il primo indirizzo/URI (spotify:, shell:…)."""
    for c in candidates:
        p = os.path.expanduser(os.path.expandvars(c))
        if os.path.exists(p):
            return p
    for c in candidates:
        if c.lower().startswith("shell:") or is_link(c):
            return c
    return None


def choice_available(c):
    """Una scelta è disponibile se esiste il percorso da controllare (o il programma)."""
    p = os.path.expanduser(os.path.expandvars(c.get("check") or c["path"]))
    return os.path.exists(p) or is_link(c["path"])


def launch_choice(c):
    path = os.path.expanduser(os.path.expandvars(c["path"]))
    args = [str(a) for a in c.get("args", [])]
    if args and not os.path.exists(path):
        raise FileNotFoundError(_("Non trovo «{path}»", path=path))
    launch(path, args or None)


class ChoicePopup(QFrame):
    """Fumetto con più scelte (pulsanti tondi) per un'app con "choices"."""

    def __init__(self, parent, choices, on_pick):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)
        for c in choices:
            text = str(c.get("label", "?"))
            b = QToolButton()
            b.setText(text)
            b.setCursor(Qt.PointingHandCursor)
            ok = choice_available(c)
            b.setToolTip(c.get("tip", text) + ("" if ok else " (" + _("non trovato") + ")"))
            b.setStyleSheet(
                f"QToolButton{{background:{T['surface2']};color:{T['ink'] if ok else T['muted']};border:none;"
                f"border-radius:19px;min-width:38px;min-height:38px;max-height:38px;padding:0 6px;"
                f"font-size:16px;font-weight:600;}}"
                f"QToolButton:hover{{background:{T['accent']};color:{T['accent_ink']};}}")
            b.clicked.connect(lambda _c=False, ch=c: (self.close(), on_pick(ch)))
            lay.addWidget(b)

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = squircle_path(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 26)
        p.fillPath(path, QColor(T["popup"]))
        p.setPen(QPen(QColor(T["line"]), 1))
        p.drawPath(path)


def _which(cmd):
    from shutil import which
    return which(cmd)


class Dock(Panel):
    def __init__(self, store):
        super().__init__("")
        self.store = store
        self.editing = False
        self.outer.setContentsMargins(14, 12, 14, 12)
        # barra visibile solo in modalità configurazione
        self.edit_bar = QWidget()
        eb = QHBoxLayout(self.edit_bar)
        eb.setContentsMargins(0, 0, 0, 0)
        eb.setSpacing(6)
        eb.addWidget(label(_("Tocca una tua app per modificarla"), "status"), 1)
        eb.addWidget(small_button(_("+ Programma"), _("Aggiungi un programma o un file"), self.add_program))
        eb.addWidget(small_button(_("+ Link"), _("Aggiungi un sito o un link"), self.add_link))
        self.lay.insertWidget(0, self.edit_bar)
        self.hint = label(_("Nessuna app. Premi la rotella ⚙ in alto per aggiungerne."), "msg", wrap=True)
        self.lay.addWidget(self.hint)
        self.grid = ResponsiveGrid(76, spacing=4, item_h=86)
        self.lay.addWidget(self.grid)
        self.icons = QFileIconProvider()
        self.set_editing(False)

    def set_editing(self, on):
        self.editing = on
        self.edit_bar.setVisible(on)
        self.stroke = "accent" if on else None
        self.stroke_w = 2.0
        self.render()
        self.update()

    def tile_clicked(self, idx, target, btn):
        if self.editing:
            self.menu(idx, btn, QPoint(btn.width() // 2, btn.height() // 2))
        else:
            self.run(target)

    def _tile(self, name, tip, icon):
        b = QToolButton()
        b.setObjectName("app")
        b.setCursor(Qt.PointingHandCursor)
        b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        b.setIconSize(QSize(TILE, TILE))
        b.setText(name if len(name) <= 10 else name[:9] + "…")
        b.setToolTip(tip)
        b.setIcon(icon)
        return b

    def _builtin_tiles(self):
        """App predefinite attive e musica preferita."""
        d = self.store.data
        presets = {**PRESET_DEFAULTS, **d.get("presets", {})}
        out = []
        defs = [PRESETS[k] for k in PRESETS if presets.get(k)]
        if d.get("music") in MUSIC:
            defs.append(MUSIC[d["music"]])
        for p in defs:
            if "choices" in p:  # app con più scelte: apre il fumetto
                b = self._tile(p["name"], p.get("tip") or _("Scegli cosa aprire"),
                               squircle_tile(TILE, p["color"], letter=p["glyph"], ink=p.get("ink", "#FFFFFF")))
                b.clicked.connect(lambda _c=False, btn=b, ch=p["choices"]: self.show_choices(btn, ch))
                out.append(b)
                continue
            target = resolve_target(p["candidates"])
            if not target:
                b = self._tile(p["name"], _("{name}: non trovato su questo computer", name=p["name"]),
                               squircle_tile(TILE, T["surface2"], letter=p["glyph"], ink=T["muted"]))
                b.clicked.connect(lambda _c=False, n=p["name"]: QMessageBox.information(
                    self, APP_NAME, _("Non trovo {name} su questo computer.", name=n)))
            else:
                b = self._tile(p["name"], _("Apri {name}", name=p["name"]), squircle_tile(TILE, p["color"], letter=p["glyph"]))
                b.clicked.connect(lambda _c=False, t=target: self.run(t))
            out.append(b)
        return out

    def show_choices(self, btn, choices):
        pop = ChoicePopup(self.window(), choices, self.pick_choice)
        pop.adjustSize()
        g = btn.mapToGlobal(QPoint(btn.width() // 2, 0))
        scr = btn.screen().availableGeometry()
        x = max(scr.left() + 8, min(g.x() - pop.width() // 2, scr.right() - pop.width() - 8))
        pop.move(x, g.y() - pop.height() - 6)
        pop.show()

    def pick_choice(self, c):
        try:
            launch_choice(c)
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, APP_NAME, _("Non riesco ad aprirlo.") + f"\n{e}")

    def render(self):
        apps = self.store.data["apps"]
        tiles = self._builtin_tiles()
        for i, a in enumerate(apps):
            name = a["name"]
            path = os.path.expanduser(a["target"])
            if not is_link(a["target"]) and os.path.exists(path):
                icon = squircle_tile(TILE, T["surface2"], icon=self.icons.icon(QFileInfo(path)))
            else:
                icon = squircle_tile(TILE, ICON_BG[sum(map(ord, name)) % len(ICON_BG)], letter=name[:1].upper())
            b = self._tile(name, _("Apri {name}", name=name) + f"\n{a['target']}", icon)
            b.clicked.connect(lambda _c=False, idx=i, t=a["target"], btn=b: self.tile_clicked(idx, t, btn))
            b.setContextMenuPolicy(Qt.CustomContextMenu)
            b.customContextMenuRequested.connect(lambda pos, idx=i, btn=b: self.menu(idx, btn, pos))
            tiles.append(b)
        self.hint.setVisible(not tiles and not self.editing)
        self.grid.setVisible(bool(tiles))
        self.grid.align_right = self.store.data.get("side") != "left"
        self.grid.set_items(tiles)

    def run(self, target):
        try:
            launch(target)
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, APP_NAME, _("Non riesco ad aprirlo.") + f"\n{e}")

    def menu(self, idx, btn, pos):
        m = QMenu(self)
        left = m.addAction(_("Sposta prima"))
        right = m.addAction(_("Sposta dopo"))
        rename = m.addAction(_("Rinomina…"))
        m.addSeparator()
        rm = m.addAction(_("Rimuovi"))
        act = m.exec(btn.mapToGlobal(pos))
        apps = self.store.data["apps"]
        if act == rm:
            apps.pop(idx)
        elif act == left and idx > 0:
            apps[idx - 1], apps[idx] = apps[idx], apps[idx - 1]
        elif act == right and idx < len(apps) - 1:
            apps[idx + 1], apps[idx] = apps[idx], apps[idx + 1]
        elif act == rename:
            name, ok = QInputDialog.getText(self, _("Rinomina"), _("Nome:"), text=apps[idx]["name"])
            if ok and name.strip():
                apps[idx]["name"] = name.strip()
        else:
            return
        self.store.save()
        self.render()

    def add_program(self):
        start = {"Windows": os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
                 "Darwin": "/Applications"}.get(SYSTEM, "/usr/share/applications")
        if SYSTEM == "Darwin":
            path = QFileDialog.getExistingDirectory(self, _("Scegli un'app"), start) or \
                   QFileDialog.getOpenFileName(self, _("Scegli un file"), start)[0]
        else:
            path = QFileDialog.getOpenFileName(self, _("Scegli il programma (anche collegamenti .lnk)"), start)[0]
        if not path:
            return
        name = Path(path).stem
        name, ok = QInputDialog.getText(self, _("Nome"), _("Come lo chiamo?"), text=name)
        if not ok:
            return
        self.store.data["apps"].append({"name": name.strip() or Path(path).stem, "target": path})
        self.store.save()
        self.render()

    def add_link(self):
        url, ok = QInputDialog.getText(self, _("Sito o link"),
                                       _("Indirizzo (es. https://mail.google.com, spotify:, discord://, steam://open/main):"))
        if not ok or not url.strip():
            return
        url = url.strip()
        if "://" not in url and ":" not in url.split("/")[0]:
            url = "https://" + url
        if url.lower().startswith(("javascript:", "data:", "file:")):
            return
        guess = url.split("://")[-1].split("/")[0].replace("www.", "").split(".")[0].capitalize() or "Link"
        name, ok = QInputDialog.getText(self, _("Nome"), _("Come lo chiamo?"), text=guess)
        if not ok:
            return
        self.store.data["apps"].append({"name": name.strip() or guess, "target": url})
        self.store.save()
        self.render()


# ---------------------------------------------------------------- grafico
class Chart(QWidget):
    def __init__(self, theme):
        super().__init__()
        self.t = theme
        self.pts = []
        self.hover = None
        self.setMinimumHeight(170)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_points(self, pts):
        self.pts = pts
        self.hover = None
        self.update()

    def _geom(self):
        r = self.rect().adjusted(4, 12, -64, -24)
        vals = [p[1] for p in self.pts]
        lo, hi = min(vals), max(vals)
        span = (hi - lo) or 1
        n = len(self.pts)

        def x(i):
            return r.left() + (0 if n == 1 else i * r.width() / (n - 1))

        def y(v):
            return r.top() + (hi - v) * r.height() / span
        return r, lo, hi, x, y

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        muted = QColor(self.t["muted"])
        if len(self.pts) < 2:
            p.setPen(muted)
            p.drawText(self.rect(), Qt.AlignCenter, _("Dati non disponibili"))
            return
        r, lo, hi, x, y = self._geom()
        up = self.pts[-1][1] >= self.pts[0][1]
        col = QColor(self.t["up"] if up else self.t["down"])
        # base
        pen = QPen(muted, 1, Qt.DashLine)
        p.setPen(pen)
        by = y(self.pts[0][1])
        p.drawLine(QPointF(r.left(), by), QPointF(r.right(), by))
        path = QPainterPath(QPointF(x(0), y(self.pts[0][1])))
        for i, (_d, v) in enumerate(self.pts[1:], 1):
            path.lineTo(QPointF(x(i), y(v)))
        area = QPainterPath(path)
        area.lineTo(QPointF(x(len(self.pts) - 1), r.bottom()))
        area.lineTo(QPointF(x(0), r.bottom()))
        area.closeSubpath()
        g = QLinearGradient(0, r.top(), 0, r.bottom())
        c1 = QColor(col); c1.setAlpha(60)
        c2 = QColor(col); c2.setAlpha(0)
        g.setColorAt(0, c1); g.setColorAt(1, c2)
        p.fillPath(area, QBrush(g))
        p.setPen(QPen(col, 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawPath(path)
        if len(self.pts) <= 6:
            p.setBrush(col)
            for i, (_d, v) in enumerate(self.pts):
                p.drawEllipse(QPointF(x(i), y(v)), 3.5, 3.5)
        f = p.font(); f.setPointSizeF(max(8.0, f.pointSizeF() - 1.5)); p.setFont(f)
        p.setPen(muted)
        p.drawText(QPointF(r.right() + 8, y(hi) + 4), it_num(hi))
        p.drawText(QPointF(r.right() + 8, y(lo) + 4), it_num(lo))
        p.drawText(QPointF(r.left(), self.height() - 6), it_short(self.pts[0][0]))
        lastlab = it_short(self.pts[-1][0])
        p.drawText(QPointF(r.right() - p.fontMetrics().horizontalAdvance(lastlab), self.height() - 6), lastlab)
        if self.hover is not None:
            i = self.hover
            p.setPen(QPen(muted, 1))
            p.drawLine(QPointF(x(i), r.top()), QPointF(x(i), r.bottom()))
            p.setBrush(col)
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(x(i), y(self.pts[i][1])), 4, 4)

    def mouseMoveEvent(self, e):
        if len(self.pts) < 2:
            return
        r, lo, hi, x, y = self._geom()
        n = len(self.pts)
        i = round((e.position().x() - r.left()) / (r.width() / (n - 1)))
        i = max(0, min(n - 1, i))
        if i != self.hover:
            self.hover = i
            self.update()
            d, v = self.pts[i]
            QToolTip.showText(e.globalPosition().toPoint(), f"{it_short(d)}  {it_num(v)}", self)

    def leaveEvent(self, _ev):
        self.hover = None
        self.update()


class RangeCard(Squircle):
    clicked = Signal(str)

    def __init__(self, key, title):
        super().__init__(radius=20, fill="surface2")
        self.key = key
        self.setCursor(Qt.PointingHandCursor)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 10, 10)
        lay.setSpacing(1)
        t = label(title, "status")
        lay.addWidget(t)
        self.val = label("–", "h3")
        lay.addWidget(self.val)

    def set_selected(self, on):
        self.stroke = "accent" if on else None
        self.stroke_w = 2.0
        self.update()

    def mousePressEvent(self, _ev):
        self.clicked.emit(self.key)


class MarketPanel(Panel):
    def __init__(self, store, theme):
        super().__init__(_("Mercati"))
        self.store, self.t = store, theme
        self.pts = []
        self.key = "mtd"
        self.results = {}   # titolo -> dati scaricati (o errore)
        self.current = None
        # schede in stile browser, una per titolo scelto
        self.tabs = QTabBar()
        self.tabs.setObjectName("tabs")
        self.tabs.setDocumentMode(True)
        self.tabs.setExpanding(False)
        self.tabs.setDrawBase(False)
        self.tabs.setElideMode(Qt.ElideRight)
        self.tabs.setUsesScrollButtons(True)
        self.tabs.setCursor(Qt.PointingHandCursor)
        self.tabs.currentChanged.connect(self.show_tab)
        self.lay.addWidget(self.tabs)
        self.msg = label(_("Scarico i dati…"), "msg", wrap=True)
        self.lay.addWidget(self.msg)
        row = QHBoxLayout()
        self.price = label("", "price")
        self.when = label("", "muted")
        row.addWidget(self.price)
        row.addWidget(self.when, 0, Qt.AlignBottom)
        row.addStretch(1)
        self.lay.addLayout(row)
        cards = QHBoxLayout()
        cards.setSpacing(8)
        self.cards = {}
        for k, title in (("d3", _("3 giorni")), ("mtd", _("Questo mese")), ("y1", _("1 anno"))):
            c = RangeCard(k, title)
            c.clicked.connect(self.select)
            cards.addWidget(c)
            self.cards[k] = c
        self.lay.addLayout(cards)
        self.chart = Chart(theme)
        self.chart.setMinimumHeight(160)
        self.lay.addWidget(self.chart, 1)
        self.head.addWidget(small_button("↻", _("Aggiorna"), self.refresh))
        self.select("mtd")
        self.set_markets()

    def markets(self):
        keys = [k for k in self.store.data.get("markets", DEFAULT_MARKETS) if k in MARKETS]
        return keys

    def set_markets(self):
        """Ricrea le schede dai titoli scelti nelle impostazioni."""
        keys = self.markets()
        keep = self.current if self.current in keys else (keys[0] if keys else None)
        self.tabs.blockSignals(True)
        while self.tabs.count():
            self.tabs.removeTab(0)
        for k in keys:
            i = self.tabs.addTab(_(MARKETS[k][0]).replace("&", "&&"))  # "&" sarebbe una scorciatoia
            self.tabs.setTabData(i, k)
        self.tabs.setVisible(len(keys) > 1)
        self.tabs.blockSignals(False)
        self.current = keep
        if keep:
            self.tabs.setCurrentIndex(keys.index(keep))
        self.show_tab()

    def show_tab(self, *_a):
        i = self.tabs.currentIndex()
        if i >= 0:
            self.current = self.tabs.tabData(i)
        keys = self.markets()
        if not keys:
            self.pts = []
            self.price.setText("")
            self.when.setText("")
            self.msg.setStyleSheet("")
            self.msg.setText(_("Nessun titolo scelto. Premi la rotella ⚙ e scegline uno in «Mercati»."))
            self.msg.show()
            self.select(self.key)
            return
        res = self.results.get(self.current)
        if res is None:
            self.pts = []
            self.price.setText("")
            self.when.setText("")
            self.msg.setStyleSheet("")
            self.msg.setText(_("Scarico i dati…"))
            self.msg.show()
            for c in self.cards.values():
                c.val.setText("–")
            self.select(self.key)
        elif "error" in res:
            self.pts = []
            self.price.setText("")
            self.when.setText("")
            for c in self.cards.values():
                c.val.setText("–")
            self.select(self.key)
            self.on_err(res["error"])
        else:
            self.on_data(res)

    def refresh(self):
        keys = self.markets()
        if keys:
            run_bg(fetch_markets, (keys,), self.on_results, self.on_err)

    def on_results(self, results):
        self.results.update(results)
        self.show_tab()

    def on_data(self, res):
        self.pts = res["points"]
        self.msg.hide()
        last = self.pts[-1]
        self.price.setText(it_num(last[1]))
        unit = MARKETS.get(self.current, (None,) * 4)[3]
        unit = _(unit) if unit else res.get("currency", "")
        self.when.setText((unit + " · " if unit else "") + it_short(last[0]))
        for k, c in self.cards.items():
            rp = range_points(self.pts, k)
            if len(rp) >= 2:
                ch = (rp[-1][1] / rp[0][1] - 1) * 100
                c.val.setText(("+" if ch >= 0 else "−") + it_num(abs(ch)) + "%")
                c.val.setStyleSheet(f"color:{self.t['up'] if ch >= 0 else self.t['down']}")
            else:
                c.val.setText("–")
        self.price.setToolTip(_("Fonte: {src}, aggiornato alle {time}", src=res["source"], time=res["fetched"]))
        self.select(self.key)

    def on_err(self, m):
        name = _(MARKETS[self.current][0]) if self.current in MARKETS else ""
        self.msg.setStyleSheet(f"color:{self.t['down']}")
        self.msg.setText(_("Non riesco a scaricare {name}. Controlla la connessione; riprovo tra 15 minuti.",
                           name=name) + "\n" + m[:200])
        self.msg.show()

    def select(self, key):
        self.key = key
        for k, c in self.cards.items():
            c.set_selected(k == key)
        self.chart.set_points(range_points(self.pts, key))


# ---------------------------------------------------------------- meteo (scheda)
class DayCard(Squircle):
    def __init__(self):
        super().__init__(radius=18, fill="surface2")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 8, 6, 8)
        lay.setSpacing(0)
        self.day = label("", "status")
        self.icon = label("")
        self.icon.setStyleSheet("font-size:22px;")
        self.temp = label("")
        self.temp.setStyleSheet("font-size:12px; font-weight:600;")
        for w in (self.day, self.icon, self.temp):
            w.setAlignment(Qt.AlignCenter)
            lay.addWidget(w)


class WeatherPanel(Panel):
    def __init__(self, store):
        super().__init__(_("Meteo"))
        self.store = store
        self.msg = label("", "msg", wrap=True)
        self.lay.addWidget(self.msg)
        self.now = QWidget()
        row = QHBoxLayout(self.now)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        self.icon = label("")
        self.icon.setStyleSheet("font-size:40px;")
        row.addWidget(self.icon)
        self.temp = label("", "price")
        row.addWidget(self.temp)
        info = QVBoxLayout()
        info.setSpacing(0)
        self.cond = label("", "h3")
        self.extra = label("", "status")
        info.addStretch(1)
        info.addWidget(self.cond)
        info.addWidget(self.extra)
        info.addStretch(1)
        row.addLayout(info, 1)
        self.lay.addWidget(self.now)
        days = QHBoxLayout()
        days.setSpacing(6)
        self.days = [DayCard() for _i in range(6)]
        for c in self.days:
            days.addWidget(c, 1)
        self.lay.addLayout(days)
        self.head.addWidget(small_button("↻", _("Aggiorna"), self.refresh))
        self.render(None)

    def location(self):
        loc = self.store.data.get("weather_loc")
        return loc if isinstance(loc, dict) and "lat" in loc else None

    def refresh(self):
        loc = self.location()
        self.set_status(loc["name"] if loc else "")
        if loc:
            run_bg(fetch_weather, (loc["lat"], loc["lon"]), self.render, self.on_err)
        else:
            self.render(None)

    def on_err(self, m):
        self.msg.setStyleSheet(f"color:{T['down']}")
        self.msg.setText(_("Non riesco a scaricare il meteo. Riprovo tra 30 minuti.") + "\n" + m[:160])
        self.msg.show()

    def render(self, j):
        has = bool(j)
        self.now.setVisible(has)
        for c in self.days:
            c.setVisible(has)
        if not has:
            if not self.location():
                self.msg.setStyleSheet("")
                self.msg.setText(_("Imposta la tua località: premi la rotella ⚙ in alto, sezione «Meteo»."))
                self.msg.show()
            return
        self.msg.hide()
        cur, daily = j.get("current", {}), j.get("daily", {})
        icon, text = wmo(cur.get("weather_code"), bool(cur.get("is_day", 1)))
        self.icon.setText(icon)
        self.temp.setText(f"{round(cur.get('temperature_2m', 0))}°")
        self.cond.setText(_(text) if text else "")
        self.extra.setText(_("Percepita {t}° · vento {w} km/h · umidità {h}%",
                             t=round(cur.get("apparent_temperature", 0)), w=round(cur.get("wind_speed_10m", 0)),
                             h=round(cur.get("relative_humidity_2m", 0))))
        self.temp.setToolTip(_("Fonte: {src}, aggiornato alle {time}", src="Open-Meteo", time=j["fetched"]))
        dates = daily.get("time", [])
        for i, c in enumerate(self.days):
            if i >= len(dates):
                c.hide()
                continue
            d = QDate.fromString(dates[i], "yyyy-MM-dd")
            c.day.setText(_("Oggi") if i == 0 else IT.toString(d, "ddd").capitalize().rstrip("."))
            ic, tx = wmo(daily["weather_code"][i])
            c.icon.setText(ic)
            c.temp.setText(f"{round(daily['temperature_2m_max'][i])}° / {round(daily['temperature_2m_min'][i])}°")
            rain = (daily.get("precipitation_probability_max") or [None] * 6)[i]
            c.setToolTip(_(tx) + (f" · {_('pioggia')} {rain}%" if rain is not None else ""))


# ---------------------------------------------------------------- calendario
TASK_DOT = "#FF9500"


class MonthCalendar(QCalendarWidget):
    """Calendario compatto disegnato a mano: i giorni fuori dal mese sono sbiaditi,
    oggi è un cerchio pieno, i giorni con impegni hanno un pallino sotto il numero."""

    def __init__(self):
        super().__init__()
        self.marks = {}  # "yyyy-MM-dd" -> {"ev", "task"}
        self.setLocale(IT)
        self.setFirstDayOfWeek(Qt.Monday)
        self.setGridVisible(False)
        self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.setHorizontalHeaderFormat(QCalendarWidget.SingleLetterDayNames)
        hf = QTextCharFormat()
        hf.setForeground(QColor(T["muted"]))
        f = QFont(); f.setPixelSize(11); f.setWeight(QFont.DemiBold)
        hf.setFont(f)
        hf.setBackground(QColor(0, 0, 0, 0) if T["glass"] else QColor(T["surface"]))
        self.setHeaderTextFormat(hf)
        for d in (Qt.Monday, Qt.Tuesday, Qt.Wednesday, Qt.Thursday, Qt.Friday, Qt.Saturday, Qt.Sunday):
            self.setWeekdayTextFormat(d, hf)
        for name, txt in (("qt_calendar_prevmonth", "‹"), ("qt_calendar_nextmonth", "›")):
            b = self.findChild(QToolButton, name)
            if b:
                b.setIcon(QIcon())
                b.setText(txt)
                b.setToolButtonStyle(Qt.ToolButtonTextOnly)
                b.setStyleSheet(f"color:{T['accent']}; font-size:18px; font-weight:600; padding:0 6px;")
        self.setMinimumHeight(215)
        if T["glass"]:
            # i widget interni riempiono lo sfondo con la palette: li rendo trasparenti
            clear = QColor(0, 0, 0, 0)
            for w in [self] + self.findChildren(QWidget):
                pal = w.palette()
                for role in (QPalette.Window, QPalette.Base, QPalette.AlternateBase, QPalette.Button):
                    pal.setColor(role, clear)
                w.setPalette(pal)
                w.setAutoFillBackground(False)
        # la rotella non deve cambiare mese: la giro alla colonna che scorre
        for w in [self] + self.findChildren(QWidget):
            w.installEventFilter(self)

    def eventFilter(self, obj, ev):
        if ev.type() == ev.Type.Wheel:
            p = self.parentWidget()
            while p is not None and not isinstance(p, QScrollArea):
                p = p.parentWidget()
            if p is not None:
                QApplication.sendEvent(p.verticalScrollBar(), ev)
            return True
        return False

    def set_marks(self, marks):
        self.marks = marks
        self.updateCells()

    def paintCell(self, p, rect, date):
        p.save()
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(rect)
        if not T["glass"]:
            p.fillRect(r, QColor(T["surface"]))
        in_month = date.month() == self.monthShown() and date.year() == self.yearShown()
        today = date == QDate.currentDate()
        sel = date == self.selectedDate()
        d = min(r.width() - 4, r.height() - 8, 26.0)
        circ = QRectF(r.center().x() - d / 2, r.top() + 1, d, d)
        ink = QColor(T["ink"])
        if today:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(T["accent"]))
            p.drawEllipse(circ)
            ink = QColor(T["accent_ink"])
        elif sel:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(T["chip"]))
            p.drawEllipse(circ)
            ink = QColor(T["chip_ink"])
        if not in_month and not today:
            ink = QColor(T["muted"])
            ink.setAlpha(110)
        f = QFont()
        f.setPixelSize(12)
        f.setWeight(QFont.Bold if (today or sel) else QFont.Normal)
        p.setFont(f)
        p.setPen(ink)
        p.drawText(circ, Qt.AlignCenter, str(date.day()))
        kinds = self.marks.get(date.toString("yyyy-MM-dd"), ())
        cols = [c for k, c in (("ev", T["accent"]), ("task", TASK_DOT)) if k in kinds]
        if cols:
            y = min(circ.bottom() + 3.5, r.bottom() - 2.5)
            x0 = r.center().x() - (len(cols) - 1) * 3.5
            for i, c in enumerate(cols):
                qc = QColor(c)
                if not in_month:
                    qc.setAlpha(110)
                p.setPen(Qt.NoPen)
                p.setBrush(qc)
                p.drawEllipse(QPointF(x0 + i * 7, y), 2.3, 2.3)
        p.restore()


class CalendarPanel(Panel):
    loaded = Signal(dict)  # giorno "yyyy-MM-dd" -> eventi, a ogni sincronizzazione

    def __init__(self, store, theme, tasks_getter):
        super().__init__(_("Calendario"), compact=True)
        self.store, self.t, self.tasks_getter = store, theme, tasks_getter
        self.days = {}
        self.head.addWidget(small_button("↻", _("Aggiorna"), self.refresh))
        self.head.addWidget(small_button("+", _("Nuovo evento in Google Calendar"), self.new_event))
        self.msg = label("", "msg", wrap=True)
        self.msg.setTextFormat(Qt.RichText)
        self.lay.addWidget(self.msg)
        self.cal = MonthCalendar()
        self.cal.selectionChanged.connect(self.render_agenda)
        self.cal.currentPageChanged.connect(lambda *_: self.cal.updateCells())
        self.lay.addWidget(self.cal)
        self.ag_title = label("", "h3")
        self.lay.addWidget(self.ag_title)
        self.agenda = AutoList()
        self.lay.addWidget(self.agenda)
        self.lay.addStretch(1)
        self.update_msg()
        self.render_agenda()

    def update_msg(self):
        if not self.store.data["ical_urls"]:
            self.msg.setText(_("Per vedere i tuoi eventi premi la rotella <b>⚙</b> in alto e poi <b>Collega Google Calendar</b>."))
            self.msg.show()
        else:
            self.msg.hide()

    def configure(self):
        text, ok = QInputDialog.getMultiLineText(
            self, _("Collega Google Calendar"), _("ISTRUZIONI_ICAL"),
            "\n".join(self.store.data["ical_urls"]))
        if not ok:
            return
        self.store.data["ical_urls"] = [u.strip() for u in text.splitlines() if u.strip()]
        self.store.save()
        self.update_msg()
        self.refresh()

    def refresh(self):
        urls = self.store.data["ical_urls"]
        if not urls:
            return
        run_bg(fetch_calendar, (urls,), self.on_data, self.on_err)

    def on_data(self, res):
        self.days = res["days"]
        note = " (" + _("{n} calendari non raggiungibili", n=len(res["errors"])) + ")" if res["errors"] else ""
        self.title.setToolTip(_("Sincronizzato alle {time}", time=res["fetched"]) + note)
        self.msg.hide()
        self.paint_days()
        self.render_agenda()
        self.loaded.emit(self.days)

    def on_err(self, m):
        self.msg.setStyleSheet(f"color:{self.t['down']}")
        self.msg.setText(_("Non riesco a leggere il calendario. Controlla la connessione e l’indirizzo iCal (⚙ → <b>Collega Google Calendar</b>). Dettaglio: ") + m[:160])
        self.msg.show()

    def paint_days(self):
        marks = {d: {"ev"} for d in self.days}
        for t in self.tasks_getter():
            if t.get("due") and not t.get("done"):
                marks.setdefault(t["due"], set()).add("task")
        self.cal.set_marks(marks)

    def render_agenda(self):
        qd = self.cal.selectedDate()
        d = qd.toString("yyyy-MM-dd")
        self.ag_title.setText(IT.toString(qd, "dddd d MMMM").capitalize())
        self.agenda.clear()
        evs = self.days.get(d, [])
        tasks = [t for t in self.tasks_getter() if t.get("due") == d and not t.get("done")]
        for e in evs:
            it = QListWidgetItem(f"{e['title']}\n{_(e['time'])}")
            if e.get("cal"):
                it.setToolTip(e["cal"])
            self.agenda.addItem(it)
        for t in tasks:
            self.agenda.addItem(QListWidgetItem(f"{t['text']}\n{_('task')}"))
        if not evs and not tasks:
            it = QListWidgetItem(_("Niente in programma."))
            it.setFlags(Qt.NoItemFlags)
            it.setForeground(QColor(self.t["muted"]))
            self.agenda.addItem(it)
        fit_list(self.agenda)

    def new_event(self):
        open_url(gcal_template(day=self.cal.selectedDate().toString("yyyy-MM-dd")))


# ---------------------------------------------------------------- task
def week_groups(days, today=None):
    """Eventi da lunedì a domenica; quelli con lo stesso nome (ricorrenti) finiscono in un solo gruppo."""
    today = today or dt.date.today()
    d = today - dt.timedelta(days=today.weekday())
    end = d + dt.timedelta(days=6)
    groups = {}
    while d <= end:
        for e in days.get(d.isoformat(), []):
            key = " ".join(e["title"].split()).casefold()
            g = groups.setdefault(key, {"title": e["title"], "items": []})
            g["items"].append((d, e["time"]))
        d += dt.timedelta(days=1)
    return list(groups.values())  # in ordine di prima comparsa


def week_when(items):
    """Quando cade un gruppo: "mar" / "mar/gio" / "mar/gio/ven", "4 volte", "tutti i giorni", poi l'orario."""
    dates = sorted({d for d, _t in items})
    abbr = lambda d: IT.toString(QDate(d.year, d.month, d.day), "ddd").rstrip(".")  # noqa: E731
    n = len(dates)
    if n >= 7:
        when = _("tutti i giorni")
    elif n >= 4:
        when = _("{n} volte", n=n)
    else:
        when = "/".join(abbr(d) for d in dates)
    times = {t for _d, t in items}
    if len(times) == 1:
        return f"{when} · {_(items[0][1])}"
    if n <= 3:  # pochi giorni con orari diversi: ogni giorno col suo orario
        return ", ".join(f"{abbr(d)} {_(t)}" for d, t in sorted(items))
    return f"{when} · " + _("orari diversi")


class TasksPanel(Panel):
    changed = Signal()

    def __init__(self, store, theme):
        super().__init__(_("Task"), compact=True)
        self.store, self.t = store, theme
        # due schede: i task e gli eventi della settimana
        self.tabs = QTabBar()
        self.tabs.setObjectName("tabs")
        self.tabs.setDocumentMode(True)
        self.tabs.setExpanding(False)
        self.tabs.setDrawBase(False)
        self.tabs.setCursor(Qt.PointingHandCursor)
        self.tabs.addTab(_("Task"))
        self.tabs.addTab(_("Questa settimana"))
        self.lay.addWidget(self.tabs)
        self.task_page = QWidget()
        tp = QVBoxLayout(self.task_page)
        tp.setContentsMargins(0, 0, 0, 0)
        tp.setSpacing(self.lay.spacing())
        top = QHBoxLayout()
        top.setSpacing(6)
        self.text = QLineEdit()
        self.text.setPlaceholderText(_("Cosa devi fare?"))
        self.text.returnPressed.connect(self.add)
        top.addWidget(self.text, 1)
        top.addWidget(small_button("+", _("Aggiungi il task"), self.add, "primary"))
        tp.addLayout(top)
        form = QHBoxLayout()
        form.setSpacing(6)
        self.has_due = QCheckBox(_("entro"))
        self.due = QDateEdit(QDate.currentDate())
        self.due.setCalendarPopup(True)
        self.due.setDisplayFormat("dd/MM/yy")
        self.due.setEnabled(False)
        self.has_due.toggled.connect(self.due.setEnabled)
        form.addWidget(self.has_due)
        form.addWidget(self.due, 1)
        tp.addLayout(form)
        self.list = AutoList()
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.menu)
        self.list.itemChanged.connect(self.toggled)
        QShortcut(QKeySequence.Delete, self.list, activated=self.delete_selected)
        tp.addWidget(self.list)
        self.lay.addWidget(self.task_page)
        self.week = AutoList()
        self.lay.addWidget(self.week)
        self.lay.addStretch(1)
        self.clear_btn = small_button(_("Pulisci"), _("Togli i task completati"), self.clear_done)
        self.head.addWidget(self.clear_btn)
        self.days = None  # arriva dal calendario
        self.render()
        self.render_week()
        self.tabs.currentChanged.connect(self.show_tab)
        self.tabs.setCurrentIndex(1 if store.data.get("tasks_tab") == "week" else 0)
        self.show_tab(self.tabs.currentIndex())

    def show_tab(self, i):
        week = i == 1
        self.task_page.setVisible(not week)
        self.clear_btn.setVisible(not week)
        self.week.setVisible(week)
        if self.store.data.get("tasks_tab", "tasks") != ("week" if week else "tasks"):
            self.store.data["tasks_tab"] = "week" if week else "tasks"
            self.store.save()

    def set_days(self, days):
        self.days = days
        self.render_week()

    def _week_note(self, text):
        it = QListWidgetItem(text)
        it.setFlags(Qt.NoItemFlags)
        it.setForeground(QColor(self.t["muted"]))
        self.week.addItem(it)

    def render_week(self):
        """Eventi da lunedì a domenica; gli eventi ricorrenti (stesso nome) stanno su una riga sola."""
        self.week.clear()
        today = dt.date.today()
        if not self.store.data["ical_urls"]:
            self._week_note(_("Collega un calendario dalle impostazioni ⚙."))
        elif self.days is None:
            self._week_note("…")
        else:
            for g in week_groups(self.days, today):
                items = g["items"]
                it = QListWidgetItem(f"{g['title']}\n{week_when(items)}")
                it.setFlags(Qt.ItemIsEnabled)
                if max(d for d, _t in items) < today:  # già passato
                    it.setForeground(QColor(self.t["muted"]))
                it.setToolTip(g["title"] + "\n" + "\n".join(
                    f"{IT.toString(QDate(d.year, d.month, d.day), 'dddd d MMM')} · {_(t)}" for d, t in items))
                self.week.addItem(it)
            if not self.week.count():
                self._week_note(_("Niente in programma."))
        fit_list(self.week)

    def tasks(self):
        return self.store.data["tasks"]

    def add(self):
        txt = self.text.text().strip()
        if not txt:
            return
        due = self.due.date().toString("yyyy-MM-dd") if self.has_due.isChecked() else ""
        self.tasks().append({"id": uuid.uuid4().hex[:10], "text": txt, "due": due, "done": False})
        self.text.clear()
        self.has_due.setChecked(False)
        self.commit()

    def commit(self):
        self.store.save()
        self.render()
        self.changed.emit()

    def render(self):
        self.list.blockSignals(True)
        self.list.clear()
        today = dt.date.today().isoformat()
        open_ = sorted([t for t in self.tasks() if not t["done"]], key=lambda t: t["due"] or "9999")
        done = [t for t in self.tasks() if t["done"]]
        for t in open_ + done:
            due = ""
            if t["due"]:
                due = "\n" + (_("oggi") if t["due"] == today else _("entro il {date}", date=it_short(t["due"])))
            it = QListWidgetItem(t["text"] + due)
            it.setToolTip(t["text"])
            it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked if t["done"] else Qt.Unchecked)
            it.setData(Qt.UserRole, t["id"])
            f = it.font()
            if t["done"]:
                f.setStrikeOut(True)
                it.setForeground(QColor(self.t["muted"]))
            elif t["due"] and t["due"] < today:
                it.setForeground(QColor(self.t["down"]))
            it.setFont(f)
            self.list.addItem(it)
        if not self.tasks():
            it = QListWidgetItem(_("Nessun task. Scrivine uno qui sopra e premi Invio."))
            it.setFlags(Qt.NoItemFlags)
            self.list.addItem(it)
        n = len(open_)
        self.set_status(_("{n} da fare", n=n) if n else "")
        fit_list(self.list)
        self.list.blockSignals(False)

    def _find(self, item):
        tid = item.data(Qt.UserRole) if item else None
        return next((t for t in self.tasks() if t["id"] == tid), None)

    def toggled(self, item):
        t = self._find(item)
        if t:
            t["done"] = item.checkState() == Qt.Checked
            QTimer.singleShot(0, self.commit)

    def delete_selected(self):
        t = self._find(self.list.currentItem())
        if t:
            self.tasks().remove(t)
            self.commit()

    def clear_done(self):
        self.store.data["tasks"] = [t for t in self.tasks() if not t["done"]]
        self.commit()

    def menu(self, pos):
        item = self.list.itemAt(pos)
        t = self._find(item)
        if not t:
            return
        m = QMenu(self)
        ren = m.addAction(_("Modifica testo…"))
        gc = m.addAction(_("Aggiungi a Google Calendar"))
        m.addSeparator()
        rm = m.addAction(_("Elimina"))
        act = m.exec(self.list.mapToGlobal(pos))
        if act == rm:
            self.tasks().remove(t)
            self.commit()
        elif act == ren:
            txt, ok = QInputDialog.getText(self, _("Modifica task"), _("Testo:"), text=t["text"])
            if ok and txt.strip():
                t["text"] = txt.strip()
                self.commit()
        elif act == gc:
            open_url(gcal_template(t["text"], t["due"] or None))


# ---------------------------------------------------------------- note
class Note(Squircle):
    def __init__(self, data, on_change, on_delete):
        super().__init__(radius=24)
        self.data = data
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 12, 10)
        self.edit = QPlainTextEdit(data.get("text", ""))
        self.edit.setPlaceholderText(_("Scrivi qui…"))
        self.edit.setFrameShape(QFrame.NoFrame)
        self.edit.textChanged.connect(lambda: (data.__setitem__("text", self.edit.toPlainText()), on_change()))
        lay.addWidget(self.edit, 1)
        bar = QHBoxLayout()
        bar.setSpacing(6)
        for name, col in NOTE_COLORS.items():
            b = QToolButton()
            b.setFixedSize(16, 16)
            b.setToolTip(_(name))
            b.setStyleSheet(f"QToolButton{{background:{col};border:1.5px solid rgba(0,0,0,.3);border-radius:8px;}}")
            b.clicked.connect(lambda _c=False, n=name: (data.__setitem__("color", n), self.paint(), on_change()))
            bar.addWidget(b)
        bar.addStretch(1)
        d = QToolButton()
        d.setText(_("Elimina"))
        d.setStyleSheet(f"QToolButton{{background:transparent;border:none;color:rgba(0,0,0,.55);padding:2px 4px;}}"
                        f"QToolButton:hover{{color:{NOTE_INK};}}")
        d.clicked.connect(lambda: on_delete(self.data))
        bar.addWidget(d)
        lay.addLayout(bar)
        self.paint()

    def paint(self):
        self.fill = NOTE_COLORS.get(self.data.get("color"), NOTE_COLORS["giallo"])
        self.setStyleSheet(f"QPlainTextEdit{{background:transparent;color:{NOTE_INK};border:none;font-size:14px;}}")
        self.update()


class NotesPanel(Panel):
    def __init__(self, store):
        super().__init__(_("Note"))
        self.store = store
        self.head.addWidget(small_button(_("+ Nota"), _("Nuova nota"), self.add, "primary"))
        self.empty = label(_("La bacheca è vuota. Premi «+ Nota» per attaccarne una."), "msg", wrap=True)
        self.lay.addWidget(self.empty)
        self.grid = ResponsiveGrid(170, spacing=12, item_h=170)
        self.lay.addWidget(self.grid)
        self.render()

    def render(self):
        notes = self.store.data["notes"]
        self.empty.setVisible(not notes)
        self.grid.setVisible(bool(notes))
        self.grid.set_items([Note(n, self.store.save, self.delete) for n in notes])

    def add(self):
        # colore casuale, diverso da quello dell'ultima nota creata
        notes = self.store.data["notes"]
        last = notes[0].get("color") if notes else None
        colors = [c for c in NOTE_COLORS if c != last] or list(NOTE_COLORS)
        n = {"id": uuid.uuid4().hex[:10], "text": "", "color": random.choice(colors)}
        self.store.data["notes"].insert(0, n)
        self.store.save()
        self.render()
        if self.grid.items:
            self.grid.items[0].edit.setFocus()

    def delete(self, data):
        if data.get("text", "").strip():
            if QMessageBox.question(self, APP_NAME, _("Eliminare questa nota?")) != QMessageBox.Yes:
                return
        self.store.data["notes"] = [n for n in self.store.data["notes"] if n is not data]
        self.store.save()
        self.render()


# ---------------------------------------------------------------- avvio automatico
def launch_command():
    if getattr(sys, "frozen", False):
        exe = sys.executable
        if SYSTEM == "Darwin" and ".app/Contents/MacOS" in exe:
            return ["open", exe.split(".app/")[0] + ".app"]
        return [exe]
    return [sys.executable, os.path.abspath(__file__)]


def autostart_path():
    home = Path.home()
    if SYSTEM == "Windows":
        return Path(os.environ.get("APPDATA", home)) / r"Microsoft\Windows\Start Menu\Programs\Startup\SiDD.lnk"
    if SYSTEM == "Darwin":
        return home / "Library/LaunchAgents/local.sidd.app.plist"
    return home / ".config/autostart/sidd.desktop"


def set_autostart(on):
    p = autostart_path()
    p.with_name(OLD_APP_NAME + p.suffix).unlink(missing_ok=True)  # collegamento col vecchio nome
    if not on:
        p.unlink(missing_ok=True)
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    cmd = launch_command()
    if SYSTEM == "Windows":
        exe = cmd[0].replace("python.exe", "pythonw.exe")
        args = " ".join(f'"{c}"' for c in cmd[1:])
        q = lambda s: s.replace("'", "''")  # noqa: E731
        ps = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%s');"
              "$s.TargetPath='%s';$s.Arguments='%s';$s.WorkingDirectory='%s';$s.Save()"
              % (q(str(p)), q(exe), q(args), q(os.path.dirname(cmd[-1]))))
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
                       check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    elif SYSTEM == "Darwin":
        items = "".join(f"<string>{c}</string>" for c in cmd)
        p.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            '<plist version="1.0"><dict><key>Label</key><string>local.sidd.app</string>'
            f'<key>ProgramArguments</key><array>{items}</array><key>RunAtLoad</key><true/></dict></plist>\n',
            encoding="utf-8")
    else:
        exec_line = " ".join(f'"{c}"' for c in cmd)
        p.write_text(f"[Desktop Entry]\nType=Application\nName=SiDD\nExec={exec_line}\n"
                     "X-GNOME-Autostart-enabled=true\n", encoding="utf-8")


# ---------------------------------------------------------------- impostazioni (modalità configurazione)
PANELS = [("notes", "Note"), ("calendar", "Calendario"), ("tasks", "Task"), ("weather", "Meteo"), ("market", "Mercati"),
          ("apps", "App")]


class SettingsPanel(Panel):
    def __init__(self, main):
        super().__init__(_("Impostazioni"))
        self.main = main
        store = main.store
        self.head.addWidget(small_button(_("Fine"), _("Esci dalla modalità configurazione"),
                                         lambda: main.set_config_mode(False), "primary"))
        self.bottom = QCheckBox(_("Resta sul desktop, sotto le altre finestre"))
        self.bottom.setChecked(bool(store.data.get("on_bottom")))
        self.bottom.toggled.connect(main.set_on_bottom)
        self.lay.addWidget(self.bottom)
        self.auto = QCheckBox(_("Apri all’avvio del computer"))
        self.auto.setChecked(autostart_path().exists())
        self.auto.toggled.connect(main.toggle_autostart)
        self.lay.addWidget(self.auto)
        self.side_btns = self.segmented(_("Lato dello schermo"), [("left", _("Sinistra")), ("right", _("Destra"))],
                                        main.set_side)
        self.theme_btns = self.segmented(_("Aspetto"), [("dark", _("Scuro")), ("light", _("Chiaro")), ("glass", _("Vetro"))], main.set_theme)
        self.lang_btns = self.segmented(_("Lingua"), LANGUAGES, main.set_language, stacked=True)

        self.section(_("Pannelli visibili"))
        hidden = set(store.data.get("hidden", []))
        grid = QGridLayout()
        grid.setSpacing(4)
        for i, (key, name) in enumerate(PANELS):
            cb = QCheckBox(_(name).replace("&", "&&"))
            cb.setChecked(key not in hidden)
            cb.toggled.connect(lambda on, k=key: main.set_panel_visible(k, on))
            grid.addWidget(cb, i // 2, i % 2)
        self.lay.addLayout(grid)

        self.section(_("App predefinite"))
        presets = {**PRESET_DEFAULTS, **store.data.get("presets", {})}
        grid = QGridLayout()
        grid.setSpacing(4)
        items = [(k, PRESETS[k]["name"]) for k in PRESETS]
        for i, (key, name) in enumerate(items):
            cb = QCheckBox(name)
            cb.setChecked(bool(presets.get(key)))
            cb.toggled.connect(lambda on, k=key: main.set_preset(k, on))
            grid.addWidget(cb, i // 2, i % 2)
        self.lay.addLayout(grid)
        self.music_btns = self.segmented(_("Musica preferita"), [("", _("Nessuna"))] + [(k, v["name"]) for k, v in MUSIC.items()],
                                         main.set_music, stacked=True)

        self.section(_("Meteo"))
        row = QHBoxLayout()
        row.setSpacing(6)
        loc = store.data.get("weather_loc")
        self.loc_label = label(loc.get("label", loc.get("name", "")) if isinstance(loc, dict) else _("Nessuna località"),
                               wrap=True)
        row.addWidget(self.loc_label, 1)
        row.addWidget(small_button(_("Cambia località…"), _("Cerca la tua città"), main.choose_location))
        self.lay.addLayout(row)

        self.section(_("Scorciatoia da tastiera"))
        row = QHBoxLayout()
        row.setSpacing(6)
        row.addWidget(label(_("Mostra / nascondi la dashboard"), wrap=True), 1)
        self.keyedit = QKeySequenceEdit(QKeySequence(store.data.get("hotkey") or ""))
        self.keyedit.setMaximumSequenceLength(1)
        self.keyedit.setFixedWidth(130)
        self.keyedit.editingFinished.connect(
            lambda: main.set_hotkey(self.keyedit.keySequence().toString(QKeySequence.PortableText)))
        row.addWidget(self.keyedit)
        row.addWidget(small_button(_("Nessuna"), _("Disattiva la scorciatoia"),
                                   lambda: (self.keyedit.clear(), main.set_hotkey(""))))
        self.lay.addLayout(row)

        self.section(_("Mercati"))
        chosen = set(store.data.get("markets", DEFAULT_MARKETS))
        grid = QGridLayout()
        grid.setSpacing(4)
        for i, (key, m) in enumerate(MARKETS.items()):
            cb = QCheckBox(_(m[0]).replace("&", "&&"))
            cb.setChecked(key in chosen)
            cb.toggled.connect(lambda on, k=key: main.set_market(k, on))
            if key.startswith("c:"):  # titolo personalizzato: si può togliere
                cell = QWidget()
                h = QHBoxLayout(cell)
                h.setContentsMargins(0, 0, 0, 0)
                h.setSpacing(4)
                cb.setToolTip(m[1])
                h.addWidget(cb)
                x = small_button("✕", _("Rimuovi {name}", name=m[0]), lambda _c=False, k=key: main.remove_market(k))
                x.setStyleSheet("padding:1px 7px; min-height:14px;")
                h.addWidget(x)
                h.addStretch(1)
                grid.addWidget(cell, i // 2, i % 2)
            else:
                grid.addWidget(cb, i // 2, i % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        self.lay.addLayout(grid)
        self.lay.addWidget(small_button(_("+ Titolo"), _("Aggiungi un titolo, un ETF, una valuta o una crypto"),
                                        main.add_market), 0, Qt.AlignLeft)

        self.section(_("Altro"))
        row = QHBoxLayout()
        row.setSpacing(6)
        row.addWidget(small_button(_("Collega Google Calendar"), _("Imposta i calendari Google"),
                                   lambda: main.calp.configure()))
        row.addWidget(small_button(_("Cartella dati"), _("Apri la cartella dei dati"),
                                   lambda: open_url(QUrl.fromLocalFile(str(store.dir)).toString())))
        row.addStretch(1)
        self.lay.addLayout(row)
        row = QHBoxLayout()
        row.setSpacing(6)
        row.addWidget(small_button(_("Cerca aggiornamenti"), _("Controlla se c’è una nuova versione su GitHub"),
                                   lambda: main.check_updates(manual=True)))
        row.addWidget(small_button(_("Ripristina impostazioni"),
                                   _("Torna alle impostazioni predefinite (note, task e app restano)"),
                                   main.restore_defaults))
        row.addStretch(1)
        self.lay.addLayout(row)
        row = QHBoxLayout()
        row.setSpacing(6)
        row.addWidget(small_button(_("Segnala un bug"), _("Scrivi cosa non funziona"), main.report_bug))
        row.addStretch(1)
        self.lay.addLayout(row)
        quit_ = small_button(_("Chiudi la dashboard"), _("Chiude il programma"), main.close)
        quit_.setStyleSheet(f"color:{T['down']};")
        self.lay.addWidget(quit_, 0, Qt.AlignLeft)
        ver = label(f"{APP_NAME} {APP_VERSION}", "status")
        self.lay.addWidget(ver)
        self.sync()

    def section(self, text):
        lb = label(text.upper(), "status")
        lb.setStyleSheet("font-weight:600; letter-spacing:0.5px; padding-top:8px;")
        self.lay.addWidget(lb)

    def segmented(self, title, options, on_pick, stacked=False):
        """Gruppo di pulsanti a capsula, uno solo acceso."""
        row = QHBoxLayout()
        row.setSpacing(6)
        btns = {}
        for key, text in options:
            b = small_button(text, text, lambda _c=False, k=key: (on_pick(k), self.sync()), "seg")
            b.setCheckable(True)
            btns[key] = b
            row.addWidget(b)
        if stacked:
            self.section(title)
            row.addStretch(1)
            self.lay.addLayout(row)
        else:
            outer = QHBoxLayout()
            outer.addWidget(label(title), 1)
            outer.addLayout(row)
            self.lay.addLayout(outer)
        return btns

    def sync(self):
        d = self.main.store.data
        for group, value in ((self.side_btns, "left" if d.get("side") == "left" else "right"),
                             (self.theme_btns, d.get("theme") if d.get("theme") in ("light", "glass") else "dark"),
                             (self.music_btns, d.get("music") if d.get("music") in MUSIC else ""),
                             (self.lang_btns, language())):
            for k, b in group.items():
                b.setChecked(k == value)


# ---------------------------------------------------------------- finestra
def theme_for(store):
    return {"light": LIGHT, "glass": GLASS}.get(store.data.get("theme"), DARK)


def enable_blur(hwnd):
    """Sfondo sfocato 'acrilico' di Windows dietro la finestra (vetro smerigliato)."""
    if SYSTEM != "Windows":
        return False
    import ctypes
    from ctypes import wintypes

    class ACCENT(ctypes.Structure):
        _fields_ = [("AccentState", ctypes.c_int), ("AccentFlags", ctypes.c_int),
                    ("GradientColor", ctypes.c_uint), ("AnimationId", ctypes.c_int)]

    class WCAD(ctypes.Structure):
        _fields_ = [("Attribute", ctypes.c_int), ("Data", ctypes.c_void_p), ("SizeOfData", ctypes.c_size_t)]

    try:
        user32 = ctypes.windll.user32
        fn = user32.SetWindowCompositionAttribute
        fn.argtypes = [wintypes.HWND, ctypes.POINTER(WCAD)]
        fn.restype = wintypes.BOOL
        # 4 = acrilico, 3 = sfocatura semplice (Windows 10 vecchi); colore in AABBGGRR
        for state, tint in ((4, 0x66141210), (3, 0x00000000)):
            accent = ACCENT(state, 0, tint, 0)
            data = WCAD(19, ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p), ctypes.sizeof(accent))
            if fn(int(hwnd), ctypes.byref(data)):
                # barra laterale: bordi dritti anche su Windows 11
                pref = ctypes.c_int(1)  # DWMWCP_DONOTROUND
                try:
                    ctypes.windll.dwmapi.DwmSetWindowAttribute(int(hwnd), 33, ctypes.byref(pref), ctypes.sizeof(pref))
                except OSError:
                    pass
                return True
    except (OSError, AttributeError):
        pass
    return False


_windows = []



def rebuild_window(old):
    global T
    T = theme_for(old.store)
    apply_language(old.store)
    sync_custom_markets(old.store)
    new = Main(old.store, config=old.gear.isChecked())
    _windows.append(new)
    new.show()
    old.hide()
    if old in _windows:
        _windows.remove(old)
    old.deleteLater()


class Main(QMainWindow):
    def __init__(self, store, config=False):
        super().__init__()
        self.store = store
        self.t = T
        self.setWindowTitle(APP_NAME)
        self.setStyleSheet(stylesheet(self.t))
        # barra laterale senza cornice, agganciata al bordo dello schermo
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint)
        if self.t["glass"]:  # vetro: finestra trasparente, sfocata da Windows (vedi showEvent)
            self.setAttribute(Qt.WA_TranslucentBackground)
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(16, 14, 8, 0)
        outer.setSpacing(10)

        # intestazione (fissa)
        head = QHBoxLayout()
        head.setContentsMargins(4, 0, 8, 0)
        # compare quando su GitHub c'è una versione più nuova
        self.release = None
        self.update_btn = small_button("", _("Scarica e installa la nuova versione"), self.do_update, "primary")
        self.update_btn.hide()
        head.addWidget(self.update_btn, 0, Qt.AlignVCenter)
        head.addStretch(1)
        btns = QVBoxLayout()
        btns.setSpacing(6)
        row = QHBoxLayout()
        row.setSpacing(6)
        self.gear = gear = QToolButton()
        gear.setObjectName("round")
        gear.setText("⚙")
        gear.setToolTip(_("Modalità configurazione: aggiungi app e cambia le impostazioni"))
        gear.setCursor(Qt.PointingHandCursor)
        gear.setCheckable(True)
        gear.toggled.connect(self.set_config_mode)
        mini = QToolButton()
        mini.setObjectName("round")
        mini.setText("–")
        mini.setToolTip(_("Riduci a icona"))
        mini.setCursor(Qt.PointingHandCursor)
        mini.clicked.connect(self.showMinimized)
        close = QToolButton()
        close.setObjectName("round")
        close.setText("✕")
        close.setToolTip(_("Chiudi SiDD"))
        close.setCursor(Qt.PointingHandCursor)
        close.clicked.connect(self.quit_app)
        row.addWidget(mini)
        row.addWidget(gear)
        row.addWidget(close)
        btns.addLayout(row)
        head.addLayout(btns)
        outer.addLayout(head)

        # colonna che scorre
        self.scroll = scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        col = QVBoxLayout(content)
        col.setContentsMargins(0, 2, 8, 16)
        col.setSpacing(12)
        scroll.setWidget(content)
        # le impostazioni si aprono sopra la colonna (overlay), non come scheda in fondo
        body = QWidget()
        self.stack = QStackedLayout(body)
        self.stack.setStackingMode(QStackedLayout.StackAll)
        self.stack.addWidget(scroll)
        outer.addWidget(body, 1)

        # app: fisse in fondo alla finestra, sempre visibili mentre il resto scorre
        self.dock = Dock(store)
        foot = QVBoxLayout()
        foot.setContentsMargins(0, 0, 8, 14)
        foot.addWidget(self.dock)
        outer.addLayout(foot)
        self.tasksp = TasksPanel(store, self.t)
        self.calp = CalendarPanel(store, self.t, lambda: store.data["tasks"])
        self.market = MarketPanel(store, self.t)
        self.notes = NotesPanel(store)
        self.weather = WeatherPanel(store)
        self.tasksp.changed.connect(lambda: (self.calp.paint_days(), self.calp.render_agenda()))
        self.calp.loaded.connect(self.tasksp.set_days)
        self.settings = SettingsPanel(self)
        self.overlay = QScrollArea()
        self.overlay.setWidgetResizable(True)
        self.overlay.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.overlay.setFrameShape(QFrame.NoFrame)
        ob = QWidget()
        ob.setObjectName("overlay")
        ol = QVBoxLayout(ob)
        ol.setContentsMargins(0, 2, 8, 16)
        ol.addWidget(self.settings)
        ol.addStretch(1)
        self.overlay.setWidget(ob)
        self.stack.addWidget(self.overlay)
        self.stack.setCurrentWidget(scroll)
        self.overlay.hide()
        self.pair = pair = QHBoxLayout()  # calendario | task
        pair.setSpacing(12)
        pair.addWidget(self.calp, 1)
        pair.addWidget(self.tasksp, 1)
        for key, w in (("notes", self.notes), ("calendar", self.calp), ("tasks", self.tasksp),
                       ("weather", self.weather), ("market", self.market)):
            w.enable_collapse(store, key)
            w.collapsedChanged.connect(self.align_pair)
        self.align_pair()
        col.addWidget(self.notes)
        col.addLayout(pair)
        col.addWidget(self.weather)
        col.addWidget(self.market)
        col.addStretch(1)

        self.tick()
        t1 = QTimer(self, interval=15_000); t1.timeout.connect(self.tick); t1.start()
        t2 = QTimer(self, interval=5 * 60_000); t2.timeout.connect(self.calp.refresh); t2.start()
        t3 = QTimer(self, interval=15 * 60_000); t3.timeout.connect(self.market.refresh); t3.start()
        t4 = QTimer(self, interval=12 * 3600_000); t4.timeout.connect(self.check_updates); t4.start()
        t5 = QTimer(self, interval=30 * 60_000); t5.timeout.connect(self.weather.refresh); t5.start()
        QTimer.singleShot(400, self.weather.refresh)
        QTimer.singleShot(4000, self.check_updates)
        QTimer.singleShot(200, self.calp.refresh)
        QTimer.singleShot(300, self.market.refresh)

        if store.data.get("on_bottom"):
            self.setWindowFlag(Qt.WindowStaysOnBottomHint, True)
        self.apply_visibility()
        self.dock_to_screen()
        app = QGuiApplication.instance()
        app.screenAdded.connect(self._redock_later)
        app.screenRemoved.connect(self._redock_later)
        app.primaryScreenChanged.connect(self._redock_later)
        scr = QGuiApplication.primaryScreen()
        if scr is not None:
            scr.availableGeometryChanged.connect(self._redock_later)
        if config:
            QTimer.singleShot(0, lambda: self.set_config_mode(True))

    # ---- aggancio al bordo
    def _redock_later(self, *_a):
        QTimer.singleShot(400, self.dock_to_screen)

    def align_pair(self, *_a):
        """Calendario e task alti uguali; se uno è ridotto, entrambi stanno in alto senza allungarsi."""
        any_collapsed = self.calp.collapsed or self.tasksp.collapsed
        flag = Qt.AlignTop if any_collapsed else Qt.AlignmentFlag(0)
        self.pair.setAlignment(self.calp, flag)
        self.pair.setAlignment(self.tasksp, flag)

    # ---- impostazioni
    def apply_visibility(self):
        hidden = set(self.store.data.get("hidden", []))
        for key, w in (("notes", self.notes), ("calendar", self.calp), ("tasks", self.tasksp),
                       ("weather", self.weather), ("market", self.market), ("apps", self.dock)):
            w.setVisible(key not in hidden)

    def set_panel_visible(self, key, on):
        hidden = set(self.store.data.get("hidden", []))
        hidden.discard(key) if on else hidden.add(key)
        self.store.data["hidden"] = [k for k, _ in PANELS if k in hidden]
        self.store.save()
        self.apply_visibility()

    def set_preset(self, key, on):
        self.store.data.setdefault("presets", {})[key] = on
        self.store.save()
        self.dock.render()

    def set_market(self, key, on):
        keys = [k for k in self.store.data.get("markets", DEFAULT_MARKETS) if k in MARKETS and k != key]
        if on:
            keys.append(key)
        self.store.data["markets"] = [k for k in MARKETS if k in keys]  # ordine fisso
        self.store.save()
        self.market.set_markets()
        if on and key not in self.market.results:
            self.market.refresh()

    # ---- meteo
    def choose_location(self):
        name, ok = QInputDialog.getText(self, _("Meteo"), _("Città o località:"))
        if not ok or not name.strip():
            return

        def found(results):
            if not results:
                QMessageBox.information(self, APP_NAME, _("Non trovo «{name}».", name=name.strip()))
                return
            pick = results[0]
            if len(results) > 1:
                labels = [r["label"] for r in results]
                choice, ok2 = QInputDialog.getItem(self, _("Meteo"), _("Quale intendi?"), labels, 0, False)
                if not ok2:
                    return
                pick = results[labels.index(choice)]
            self.store.data["weather_loc"] = pick
            self.store.save()
            self.settings.loc_label.setText(pick["label"])
            self.weather.refresh()

        def fail(m):
            QMessageBox.warning(self, APP_NAME, _("Non riesco a cercare la località.") + f"\n{m[:200]}")
        run_bg(geocode, (name.strip(),), found, fail)

    # ---- mercati personalizzati
    def add_market(self):
        sym, ok = QInputDialog.getText(self, _("Nuovo titolo"), _(
            "Simbolo come su Yahoo Finance (es. AAPL, ENI.MI, EURUSD=X, ETH-USD, ^STOXX50E):"))
        sym = sym.strip().upper()
        if not ok or not sym:
            return
        if "c:" + sym in MARKETS:
            return
        name, ok = QInputDialog.getText(self, _("Nuovo titolo"), _("Nome da mostrare:"), text=sym)
        if not ok:
            return

        def done(_res):
            self.store.data.setdefault("custom_markets", []).append({"symbol": sym, "name": name.strip() or sym})
            self.store.data.setdefault("markets", list(DEFAULT_MARKETS)).append("c:" + sym)
            sync_custom_markets(self.store)
            self.store.save_now()
            QTimer.singleShot(0, lambda: rebuild_window(self))

        def fail(m):
            QMessageBox.warning(self, APP_NAME, _("Non trovo il simbolo «{sym}» su Yahoo Finance.", sym=sym)
                                + f"\n{m[:200]}")
        run_bg(_yahoo, (sym,), done, fail)

    def remove_market(self, key):
        sym = key[2:]
        d = self.store.data
        d["custom_markets"] = [c for c in d.get("custom_markets", []) if c.get("symbol") != sym]
        d["markets"] = [k for k in d.get("markets", []) if k != key]
        sync_custom_markets(self.store)
        self.store.save_now()
        QTimer.singleShot(0, lambda: rebuild_window(self))

    # ---- scorciatoia
    def set_hotkey(self, text):
        old = self.store.data.get("hotkey", "")
        if text == old:
            return
        if set_global_hotkey(text):
            self.store.data["hotkey"] = text
            self.store.save()
        else:
            set_global_hotkey(old)
            self.settings.keyedit.setKeySequence(QKeySequence(old, QKeySequence.PortableText))
            QMessageBox.warning(self, APP_NAME, _("Non posso usare questa combinazione: serve almeno Ctrl, Alt o Win "
                                                  "più una lettera, un numero o un tasto F, e non deve essere già "
                                                  "usata da un altro programma."))

    # ---- segnalazione bug
    def report_bug(self):
        dlg = BugDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        text = dlg.text.toPlainText().strip()
        if not text:
            return
        info = system_info() if dlg.info.isChecked() else ""
        contact = dlg.contact.text().strip()
        if not BUG_REPORT_URL:
            open_url(github_issue_url(text, info))
            return

        def fail(m):
            if QMessageBox.question(self, APP_NAME, _("Invio non riuscito. Apro la pagina delle segnalazioni su "
                                                      "GitHub?") + f"\n{m[:200]}") == QMessageBox.Yes:
                open_url(github_issue_url(text, info))
        run_bg(send_bug_report, (text, contact, info),
               lambda _ok: QMessageBox.information(self, APP_NAME, _("Grazie! Segnalazione inviata.")), fail)

    # ---- aggiornamenti
    def check_updates(self, manual=False):
        if not update_repo():
            if manual:
                QMessageBox.information(self, APP_NAME, _("Questa è una build personalizzata: gli aggiornamenti "
                                                          "automatici sono disattivati."))
            return

        def done(rel):
            newer = rel and rel.get("version") and version_tuple(rel["version"]) > version_tuple(APP_VERSION)
            if newer:
                self.release = rel
                self.update_btn.setText(_("⬆ Aggiorna a {v}", v=rel["version"]))
                self.update_btn.show()
            elif manual:
                QMessageBox.information(self, APP_NAME, _("Hai già l’ultima versione ({v}).", v=APP_VERSION))

        def fail(m):
            if manual:
                QMessageBox.warning(self, APP_NAME, _("Non riesco a controllare gli aggiornamenti.") + f"\n{m[:200]}")
        run_bg(fetch_latest_release, (), done, fail)

    def do_update(self):
        rel = self.release
        if not rel:
            return
        if not getattr(sys, "frozen", False) or not rel.get("url"):
            open_url(rel["page"])  # dal sorgente (o senza exe allegato): apro la pagina della release
            return
        notes = rel["notes"].strip()
        msg = _("Scaricare e installare {app} {v}? Il programma si riavvia da solo.", app=APP_NAME, v=rel["version"])
        if notes:
            msg += "\n\n" + notes[:600]
        if QMessageBox.question(self, APP_NAME, msg) != QMessageBox.Yes:
            return
        self.update_btn.setEnabled(False)
        self.update_btn.setText(_("Scarico…"))

        def done(path):
            try:
                install_update(path)
            except OSError as e:
                fail(str(e))
                return
            self.close()
            QApplication.quit()

        def fail(m):
            self.update_btn.setEnabled(True)
            self.update_btn.setText(_("⬆ Aggiorna a {v}", v=rel["version"]))
            QMessageBox.warning(self, APP_NAME, _("Aggiornamento non riuscito.") + f"\n{m[:200]}")
        run_bg(download_update, (rel["url"], rel["size"]), done, fail)

    def restore_defaults(self):
        """Riporta le impostazioni a quelle iniziali; note, task, app e calendari restano."""
        if QMessageBox.question(self, APP_NAME, _("Ripristinare le impostazioni predefinite?\n"
                                                  "Note, task, app e calendari non vengono toccati.")) != QMessageBox.Yes:
            return
        for k in Store.SETTINGS:
            self.store.data[k] = json.loads(json.dumps(Store.DEFAULTS[k]))
        self.store.save_now()
        set_global_hotkey(self.store.data["hotkey"])
        try:
            set_autostart(True)
        except (OSError, subprocess.SubprocessError):
            pass
        self.setWindowFlag(Qt.WindowStaysOnBottomHint, False)
        QTimer.singleShot(0, lambda: rebuild_window(self))

    def set_music(self, key):
        self.store.data["music"] = key
        self.store.save()
        self.dock.render()

    def set_language(self, code):
        if self.store.data.get("lang", "it") == code:
            return
        self.store.data["lang"] = code
        self.store.save_now()
        QTimer.singleShot(0, lambda: rebuild_window(self))

    def set_theme(self, name):
        if self.store.data.get("theme", "dark") == name:
            return
        self.store.data["theme"] = name
        self.store.save_now()
        # i colori sono "cotti" nei widget: ricostruisco la finestra col nuovo tema
        QTimer.singleShot(0, lambda: rebuild_window(self))

    def dock_to_screen(self):
        scr = QGuiApplication.primaryScreen()
        if scr is None:
            return
        g = scr.availableGeometry()  # schermo meno la barra delle applicazioni
        w = round(g.width() * DOCK_WIDTH)
        x = g.left() if self.store.data.get("side") == "left" else g.right() - w + 1
        self.setMinimumSize(0, 0)
        self.setGeometry(x, g.top(), w, g.height())
        self.setFixedSize(w, g.height())

    def set_side(self, side):
        self.store.data["side"] = side
        self.store.save()
        self.settings.sync()
        self.dock.grid.set_align_right(side != "left")
        self.dock_to_screen()

    def set_config_mode(self, on):
        if self.gear.isChecked() != on:
            self.gear.setChecked(on)  # richiama questa funzione tramite toggled
            return
        self.overlay.setVisible(on)
        if on:
            self.stack.setCurrentWidget(self.overlay)  # sopra la colonna
            self.overlay.verticalScrollBar().setValue(0)
        self.dock.set_editing(on)

    def tick(self):
        now = dt.datetime.now()
        self.calp.set_status(IT.toString(QDate.currentDate(), "dddd d MMMM yyyy").capitalize())
        if now.hour == 0 and now.minute == 0:
            self.calp.paint_days()

    def set_on_bottom(self, on):
        self.store.data["on_bottom"] = on
        self.store.save()
        self.setWindowFlag(Qt.WindowStaysOnBottomHint, on)
        self.show()
        self.dock_to_screen()

    def toggle_autostart(self, on):
        try:
            set_autostart(on)
        except (OSError, subprocess.SubprocessError) as e:
            QMessageBox.warning(self, APP_NAME, _("Non riesco a cambiare l’avvio automatico.") + f"\n{e}")

    def showEvent(self, e):
        super().showEvent(e)
        # la finestra nativa può essere ricreata (es. "sempre sotto"): riapplico la sfocatura
        if self.t["glass"] and not getattr(self, "_blur_retry", False):
            self._apply_blur()

    def _apply_blur(self, tries=0):
        """Vetro: sfocatura di Windows. All'accensione del PC può non essere ancora pronta: sfondo pieno
        provvisorio per restare leggibile e nuovi tentativi, poi si torna al vetro."""
        solid = getattr(self, "_solid", False)
        self._blur_retry = False
        if enable_blur(self.winId()):
            if solid:
                self._solid = False
                self.setStyleSheet(stylesheet(self.t))
            return
        if not solid:
            self._solid = True
            self.setStyleSheet(self.styleSheet() + "#root { background:#E6141416; }")
        if tries < 60:  # per circa 2 minuti
            self._blur_retry = True

            def again():
                try:
                    self._apply_blur(tries + 1)
                except RuntimeError:  # finestra ricostruita nel frattempo (cambio tema/lingua)
                    pass
            QTimer.singleShot(2000, again)

    def closeEvent(self, e):
        self.store.save_now()
        super().closeEvent(e)

    def quit_app(self):
        self.store.save_now()
        QApplication.quit()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("")
    global T
    store = Store()
    T = theme_for(store)
    apply_language(store)
    sync_custom_markets(store)
    # scorciatoia globale per mostrare/nascondere la barra
    app._hotkeys = HotkeyFilter()
    app.installNativeEventFilter(app._hotkeys)
    set_global_hotkey(store.data.get("hotkey") or "")
    win = Main(store)
    _windows.append(win)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
