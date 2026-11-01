"""Regenerate THIRD-PARTY-NOTICES.txt for the components bundled into Grandmist.exe.

Run after changing dependencies:  python tools/third_party_notices.py
Licence texts are copied from the installed packages, so the file matches what PyInstaller bundles.
"""
import importlib.metadata as md
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGES = ['pywebview', 'pythonnet', 'clr_loader', 'bottle', 'proxy_tools', 'cryptography', 'cffi', 'pycparser', 'pyinstaller']
MANUAL = [
    ('Microsoft Edge WebView2 SDK (Microsoft.Web.WebView2.*.dll, WebView2Loader.dll)',
     'Copyright (C) Microsoft Corporation. Distributed with pywebview under the Microsoft WebView2 SDK licence: '
     'https://www.nuget.org/packages/Microsoft.Web.WebView2/ (see "License")'),
    ('Microsoft Visual C++ runtime (VCRUNTIME140.dll, VCRUNTIME140_1.dll)',
     'Copyright (C) Microsoft Corporation. Redistributable runtime files shipped with Python for Windows: '
     'https://learn.microsoft.com/cpp/windows/redistributing-visual-cpp-files'),
    ('Chess piece graphics',
     'Colin M.L. Burnett (cburnett), https://commons.wikimedia.org/wiki/Category:SVG_chess_pieces - '
     'available under GPLv2-or-later, GFDL and CC BY-SA 3.0.'),
]


def licence_texts(dist):
    out = []
    for f in dist.files or []:
        name = os.path.basename(str(f)).upper()
        if name.startswith(('LICENSE', 'LICENCE', 'COPYING', 'NOTICE')):
            try:
                out.append(open(dist.locate_file(f), encoding='utf-8', errors='replace').read().strip())
            except OSError:
                pass
    return out


def main():
    parts = ['Grandmist bundles the following third-party components. Engines such as Stockfish or Lc0 are NOT bundled;',
             'users download and load them separately.', '']
    py_licence = os.path.join(sys.base_prefix, 'LICENSE.txt')
    parts += ['=' * 78, f'Python {sys.version.split()[0]} (includes OpenSSL, libffi, bzip2, xz, zstd and others)', '=' * 78,
              open(py_licence, encoding='utf-8', errors='replace').read().strip(), '']
    for name in PACKAGES:
        try:
            dist = md.distribution(name)
        except md.PackageNotFoundError:
            continue
        meta = dist.metadata
        lic = meta.get('License-Expression') or (meta.get('License') or '').splitlines()[0:1]
        parts += ['=' * 78, f'{dist.name} {dist.version} - {lic if isinstance(lic, str) else "".join(lic)}',
                  meta.get('Home-page') or '', '=' * 78]
        parts += licence_texts(dist) or ['(licence text: see the project page above)']
        parts.append('')
    for title, text in MANUAL:
        parts += ['=' * 78, title, '=' * 78, text, '']
    path = os.path.join(ROOT, 'THIRD-PARTY-NOTICES.txt')
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(parts))
    print('wrote', path)


if __name__ == '__main__':
    main()
