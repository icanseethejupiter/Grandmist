# Grandmist

A lightweight chess database for Windows — think a pared-down ChessBase for building and studying your own repertoire.

- **`.gm` files** — one file holds a whole collection: every record, category, variation and comment. Create, open and save them like any document, and manage them in Windows Explorer
- **Variations & comments** — play a different move anywhere to branch; annotate with comments and `!` `?` `±` symbols
- **Opening tree** — moves played from the current position across your library, with results, transpositions included
- **Tree view** — the whole library drawn as a real tree; hover to preview a position, click to jump
- **PGN import / export** — variations and comments preserved; works with ChessBase, Lichess and others
- **Languages** — English, Chinese and Russian built in; add more by dropping a translated `xx.json` into a `lang` folder next to the exe

## Download

Get `Grandmist.exe` from [Releases](../../releases) and run it. Use **File > Save** (Ctrl+S) to save your work as a `.gm` file; files go to `Documents\Grandmist` by default. After the first launch, double-clicking any `.gm` file opens it in Grandmist.

## Run from source / build

Requires Python 3.10+:

```bash
pip install pywebview pyinstaller
python main.py      # run
build.bat           # build dist\Grandmist.exe
```

## Project layout

| File | Purpose |
| --- | --- |
| `app/index.html` | The entire UI, rules engine and PGN parser |
| `app/lang/` | Language packs (`en.json` is the reference; copy it to translate) |
| `main.py` | Desktop shell (pywebview): file storage and dialogs |
| `build.bat` | Build script |
| `assets/` | App and file icon (`tools/make_icon.py` regenerates it) |

## Credits

- Chess pieces by Colin M.L. Burnett (cburnett), licensed [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).
- Developed with AI assistance using [Claude Code](https://claude.com/claude-code).
