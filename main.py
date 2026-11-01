"""Grandmist desktop shell.

The whole UI lives in app/index.html. This file only:
  * opens a desktop window showing it (pywebview, backed by Edge WebView2 on Windows)
  * reads and writes .gm documents and shows the native open / save dialogs
  * registers the .gm file type so double-clicking a file opens it in Grandmist
  * loads language packs: built into the exe, plus any xx.json in a "lang" folder next to it
  * keeps app settings in %APPDATA%\\Grandmist (never next to the user's files)
"""
import ctypes
import glob
import json
import os
import subprocess
import sys
import threading
import urllib.error
import urllib.request

import webview

APP_TITLE = 'Grandmist'
EXT = '.gm'
PROG_ID = 'Grandmist.gm'
# Library locations used by v1.1.0; its records are offered once as "My Library"
ALLOWED_URLS = ('https://lichess.org/api/', 'https://api.chess.com/pub/')
LEGACY_FOLDERS = ('Grandmist Data', '\u68cb\u8c31\u6570\u636e')


def app_dir():
    """Folder containing the exe (or this file when run with python)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resource_path(*parts):
    """Files bundled into the exe are unpacked to sys._MEIPASS."""
    return os.path.join(getattr(sys, '_MEIPASS', app_dir()), *parts)


def documents_dir():
    """Documents\\Grandmist, following the real Documents location (it may be on OneDrive)."""
    buf = ctypes.create_unicode_buffer(260)
    ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf)  # 5 = CSIDL_PERSONAL
    d = os.path.join(buf.value or os.path.expanduser('~'), 'Grandmist')
    os.makedirs(d, exist_ok=True)
    return d


SETTINGS_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'Grandmist')
os.makedirs(SETTINGS_DIR, exist_ok=True)
SETTINGS = os.path.join(SETTINGS_DIR, 'settings.json')


def read_text(path):
    raw = open(path, 'rb').read()
    for enc in ('utf-8-sig', 'gb18030'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode('latin-1')


def write_text(path, text):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(text)
    os.replace(tmp, path)


def dialog_kind(name):
    # pywebview 5+ uses FileDialog.OPEN / SAVE; older versions use OPEN_DIALOG / SAVE_DIALOG
    fd = getattr(webview, 'FileDialog', None)
    return getattr(fd, name) if fd else getattr(webview, name + '_DIALOG')


def first_path(result):
    if not result:
        return None
    return result if isinstance(result, str) else result[0]


def register_file_type():
    """Point .gm files at this exe for the current user (no admin rights needed)."""
    import winreg
    exe = sys.executable
    command = f'"{exe}" "%1"'
    base = r'Software\Classes'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, rf'{base}\{PROG_ID}\shell\open\command') as k:
            if winreg.QueryValue(k, None) == command:
                return
    except OSError:
        pass
    values = {
        rf'{base}\{EXT}': PROG_ID,
        rf'{base}\{PROG_ID}': 'Grandmist chess file',
        rf'{base}\{PROG_ID}\DefaultIcon': f'"{exe}",0',
        rf'{base}\{PROG_ID}\shell\open\command': command,
    }
    for key, value in values.items():
        winreg.SetValue(winreg.HKEY_CURRENT_USER, key, winreg.REG_SZ, value)
    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)  # refresh Explorer icons


class Engine:
    """Runs one UCI engine (Lc0, Stockfish, ...) as a child process and keeps its latest analysis.

    UCI is a plain-text protocol: we write commands to the engine's stdin ("position ...", "go infinite",
    "stop") and read "info ..." lines from its stdout. The page polls snapshot() a few times a second.
    """

    def __init__(self):
        self.proc = None
        self.path = None
        self.name = ''
        self.options = set()
        self.lock = threading.Lock()
        self.uciok = threading.Event()
        self.readyok = threading.Event()
        self.bestmove = threading.Event()
        self.searching = False
        self.fen = None
        self.lines = {}
        self.error = None

    def _send(self, cmd):
        self.proc.stdin.write(cmd + '\n')
        self.proc.stdin.flush()

    def _reader(self, proc):
        for raw in proc.stdout:
            line = raw.strip()
            if line.startswith('id name '):
                self.name = line[8:]
            elif line.startswith('option name '):
                self.options.add(line[12:].split(' type ')[0])
            elif line == 'uciok':
                self.uciok.set()
            elif line == 'readyok':
                self.readyok.set()
            elif line.startswith('bestmove'):
                self.bestmove.set()
            elif line.startswith('info ') and ' pv ' in line and self.searching:
                self._parse_info(line.split())
        if proc is self.proc:
            self.error = 'engine stopped'
            self.searching = False

    def _parse_info(self, tok):
        d = {}
        i = 1
        while i < len(tok):
            k = tok[i]
            if k in ('depth', 'seldepth', 'multipv', 'nodes', 'nps'):
                d[k] = int(tok[i + 1]); i += 2
            elif k == 'score':
                d['score'] = [tok[i + 1], int(tok[i + 2])]; i += 3  # ["cp", 35] or ["mate", -3]
                while i < len(tok) and tok[i] in ('lowerbound', 'upperbound'):
                    i += 1
            elif k == 'wdl':
                d['wdl'] = [int(tok[i + 1]), int(tok[i + 2]), int(tok[i + 3])]; i += 4
            elif k == 'pv':
                d['pv'] = tok[i + 1:]; break
            else:
                i += 1
        if 'pv' in d and 'score' in d:
            self.lines[d.get('multipv', 1)] = d

    def start(self, path):
        with self.lock:
            self.quit()
            flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            self.proc = subprocess.Popen(
                [path], cwd=os.path.dirname(path) or None, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', bufsize=1, creationflags=flags)
            self.path, self.name, self.error = path, os.path.basename(path), None
            self.options = set()
            self.uciok.clear(); self.readyok.clear()
            threading.Thread(target=self._reader, args=(self.proc,), daemon=True).start()
            self._send('uci')
            if not self.uciok.wait(20):
                self.quit()
                raise RuntimeError('not a UCI engine (no "uciok" reply)')
            for name, value in (('MultiPV', 3), ('UCI_ShowWDL', 'true')):
                if name in self.options:
                    self._send(f'setoption name {name} value {value}')
            self._send('isready')
            self.readyok.wait(90)  # Lc0 loads its neural network here; this can take a while
            return {'name': self.name, 'path': path}

    def analyze(self, fen):
        with self.lock:
            if not self.proc or self.proc.poll() is not None:
                raise RuntimeError('engine is not running')
            self._stop_search()
            self.fen, self.lines = fen, {}
            self._send(f'position fen {fen}')
            self._send('go infinite')
            self.searching = True

    def _stop_search(self):
        if self.searching:
            self.bestmove.clear()
            self._send('stop')
            self.bestmove.wait(5)
            self.searching = False

    def stop(self):
        with self.lock:
            if self.proc and self.proc.poll() is None:
                self._stop_search()

    def quit(self):
        proc, self.proc, self.searching = self.proc, None, False
        if proc and proc.poll() is None:
            try:
                proc.stdin.write('quit\n'); proc.stdin.flush()
                proc.wait(3)
            except (OSError, subprocess.TimeoutExpired):
                proc.kill()

    def snapshot(self):
        lines = [self.lines[k] for k in sorted(self.lines)]
        return {'name': self.name, 'fen': self.fen, 'running': bool(self.proc and self.proc.poll() is None),
                'searching': self.searching, 'error': self.error, 'lines': lines}


ENGINE = Engine()


def load_core():
    """Optional private core module. Absent in public builds; every public feature works without it.

    Release builds bundle it only as a compiled binary module. When running from source, a sibling
    grandmist-core folder is used if it exists.
    """
    if not getattr(sys, 'frozen', False):
        dev = os.path.join(os.path.dirname(app_dir()), 'grandmist-core')
        if os.path.isdir(dev):
            sys.path.insert(0, dev)
    try:
        import grandmist_core
        return grandmist_core
    except ImportError:
        return None


CORE = load_core()


class Api:
    """Methods callable from the page as window.pywebview.api.xxx()."""

    def __init__(self):
        self._window = None
        self._dirty = False
        # Replaced by the page with the current language (see setLanguage in index.html)
        self._strings = {'close_title': 'Unsaved changes', 'close_msg': 'This file has unsaved changes. Close Grandmist without saving?',
                         'ft_gm': 'Grandmist files', 'ft_pgn': 'PGN files', 'ft_exe': 'Engines', 'ft_all': 'All files'}

    def _types(self, *kinds):
        patterns = {'gm': '*.gm', 'pgn': '*.pgn', 'exe': '*.exe', 'all': '*.*'}
        return tuple(f"{self._strings['ft_' + k]} ({patterns[k]})" for k in kinds)

    def set_strings(self, strings):
        self._strings.update(strings)

    def get_languages(self):
        packs = {}
        for folder in (resource_path('app', 'lang'), os.path.join(app_dir(), 'lang')):
            for f in sorted(glob.glob(os.path.join(folder, '*.json'))):
                code = os.path.splitext(os.path.basename(f))[0]
                if code.startswith('_'):
                    continue  # templates
                try:
                    pack = json.loads(read_text(f))
                except ValueError:
                    continue  # skip a broken pack instead of failing to start
                packs.setdefault(code, {}).update(pack)
        return packs

    def open_lang_folder(self):
        """Create the lang folder next to the exe with an English template to translate."""
        folder = os.path.join(app_dir(), 'lang')
        os.makedirs(folder, exist_ok=True)
        template = os.path.join(folder, '_template.json')
        if not os.path.exists(template):
            with open(resource_path('app', 'lang', 'en.json'), encoding='utf-8') as src:
                write_text(template, src.read())
        os.startfile(folder)

    def startup(self):
        arg = next((a for a in sys.argv[1:] if os.path.isfile(a)), None)
        legacy = None
        for folder in LEGACY_FOLDERS:
            lib = os.path.join(app_dir(), folder, 'library.json')
            if os.path.isfile(lib):
                legacy = read_text(lib)
                os.replace(lib, lib + '.imported')  # offer it only once; the file itself is kept
                break
        return {'file': os.path.abspath(arg) if arg else None, 'legacy': legacy}

    def load_settings(self):
        return read_text(SETTINGS) if os.path.exists(SETTINGS) else None

    def save_settings(self, text):
        write_text(SETTINGS, text)

    def read_file(self, path):
        return read_text(path) if os.path.isfile(path) else None

    def write_file(self, path, text):
        write_text(path, text)
        return True

    def open_dialog(self):
        path = first_path(self._window.create_file_dialog(dialog_kind('OPEN'), directory=documents_dir(), file_types=self._types('gm', 'pgn', 'all')))
        if not path:
            return None
        return {'path': path, 'name': os.path.basename(path), 'text': read_text(path)}

    def save_dialog(self, name, text):
        path = first_path(self._window.create_file_dialog(
            dialog_kind('SAVE'), directory=documents_dir(), save_filename=name, file_types=self._types('gm')))
        if not path:
            return None
        if not path.lower().endswith(EXT):
            path += EXT
        write_text(path, text)
        return path

    def save_pgn(self, name, text):
        path = first_path(self._window.create_file_dialog(
            dialog_kind('SAVE'), directory=documents_dir(), save_filename=name, file_types=self._types('pgn', 'all')))
        if not path:
            return None
        if not path.lower().endswith('.pgn'):
            path += '.pgn'
        write_text(path, text)
        return path

    def open_pgn(self):
        result = self._window.create_file_dialog(
            dialog_kind('OPEN'), directory=documents_dir(), allow_multiple=True, file_types=self._types('pgn', 'all'))
        if not result:
            return []
        return [{'name': os.path.basename(p), 'text': read_text(p)} for p in result]

    def set_window(self, title, dirty):
        self._dirty = bool(dirty)
        self._window.set_title(title)

    # ---------- optional core ----------
    def core_info(self):
        if CORE is None:
            return {'available': False}
        return {'available': True, **CORE.info()}

    def core_call(self, name, args=None):
        if CORE is None:
            return {'ok': False, 'error': 'core not available'}
        return CORE.call(name, args)

    # ---------- engines ----------
    def engine_pick(self):
        return first_path(self._window.create_file_dialog(dialog_kind('OPEN'), file_types=self._types('exe', 'all')))

    def engine_start(self, path):
        try:
            return {'ok': True, **ENGINE.start(path)}
        except (OSError, RuntimeError) as e:
            return {'ok': False, 'error': str(e)}

    def engine_analyze(self, fen):
        try:
            ENGINE.analyze(fen)
            return True
        except (OSError, RuntimeError) as e:
            return str(e)

    def engine_stop(self):
        ENGINE.stop()

    def engine_poll(self):
        return ENGINE.snapshot()

    # ---------- downloads (Lichess / Chess.com public APIs only) ----------
    def fetch(self, url, accept='application/x-chess-pgn'):
        if not url.startswith(ALLOWED_URLS):
            return {'ok': False, 'status': 0, 'error': 'address not allowed'}
        req = urllib.request.Request(url, headers={'User-Agent': 'Grandmist chess database', 'Accept': accept})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return {'ok': True, 'status': r.status, 'text': r.read().decode('utf-8', 'replace')}
        except urllib.error.HTTPError as e:
            return {'ok': False, 'status': e.code, 'error': str(e)}
        except (urllib.error.URLError, OSError) as e:
            return {'ok': False, 'status': 0, 'error': str(e)}

    def show_in_folder(self, path):
        subprocess.Popen(['explorer', '/select,', os.path.normpath(path)])


def main():
    if getattr(sys, 'frozen', False):
        try:
            register_file_type()
        except OSError:
            pass  # the app still works without the file association
    api = Api()
    window = webview.create_window(
        APP_TITLE, resource_path('app', 'index.html'), js_api=api,
        width=1440, height=900, min_size=(1000, 640), background_color='#0b0e12',
    )
    api._window = window

    def on_closing():
        if api._dirty:
            return window.create_confirmation_dialog(api._strings['close_title'], api._strings['close_msg'])
        return True

    window.events.closing += on_closing
    window.events.closed += ENGINE.quit
    webview.start(private_mode=False, storage_path=os.path.join(SETTINGS_DIR, 'webview'))


if __name__ == '__main__':
    main()
