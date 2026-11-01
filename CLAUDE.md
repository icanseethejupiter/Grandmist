# Grandmist

Chess visualization desktop app for Windows, aimed at English-speaking users. This is the **public shell**.

## Layout
- `app/index.html`: entire UI, rules engine and PGN parser in one file, no external dependencies
- `app/lang/*.json`: language packs
- `main.py`: pywebview shell; reads/writes `.gm` files, native dialogs, `.gm` file type registration, UCI engine hosting, Lichess / Chess.com downloads, optional core module
- `build.bat`: builds `dist\Grandmist.exe` (icon from `assets/grandmist.ico`, made by `tools/make_icon.py`)
- Repo: https://github.com/icanseethejupiter/Grandmist (private until a licence is chosen)
- Feature status: `ROADMAP.md` (public features only)

## Document model (like XQStudio's .xql)
- One `.gm` file = one self-contained collection: every record with its categories, variations and comments. JSON: `{format: "grandmist", version: 1, lastOpen, records: [{id, pgn, updated}]}`; each record is PGN with custom `Title` / `Category` tags.
- The app edits one file at a time: File > New / Open / Save / Save As. Users manage files in Windows Explorer; no hidden database.
- App settings live in `%APPDATA%\Grandmist\settings.json`, never next to user files. Default save folder: `Documents\Grandmist`.

## Public vs core
- Grandmist has a **private core** in a separate repository and folder. This public repo must never contain core code, core ideas or their wording (not in files, README, ROADMAP, release notes or commit messages).
- **Before building any new feature, ask the user whether it belongs to the public shell or the core.** Core work happens only in the private core repository (see its own CLAUDE.md).
- The shell talks to the core only through `Api.core_info()` / `Api.core_call()` in `main.py`. Without the core, every public feature must keep working.
- Release builds include the core only as a compiled binary module, never as .py / .pyc.
- A local pre-push hook checks every push for core content; never bypass it. If it blocks a push, remove the content instead.
- Release notes describe features only, never how they work.
- No API keys anywhere in this repo or in the exe.

## Rules
- **Everything in the product is English** by default: code comments, README, commit messages, release notes. The only non-English text lives in translation packs (`app/lang/*.json`).
- **All UI text goes through the language packs**: never hard-code visible text in `index.html`; add a key to `app/lang/en.json` and use `t('key', { vars })` or a `data-i18n` attribute, then add the same key to every other pack (`zh`, `ru`, ...). Plurals use objects like `{ "one": ..., "other": ... }` (Russian also needs `few` / `many`).
- Language packs: built-in ones are bundled into the exe; users can drop `xx.json` into a `lang` folder next to the exe to add or override a language.
- **Talk to the user in Chinese**, in plain words; they are new to programming.
- **After every completed change, commit and push to origin/main** without asking. The first line of the commit message says clearly what changed.
- Edit only what needs to change; don't rewrite whole files (saves tokens).
- Verify UI changes in the browser before rebuilding the exe.
- **Never publish a GitHub Release unless the user explicitly asks for one.**
- **Never commit secrets or user data**: no keys, tokens, certificates, `.env` files, `library.json`, `.gm` or `.pgn` files. Check `git status` before every commit.
- Keep the `.gm` format backward compatible: new versions must still open old files.
- Don't force-close a running Grandmist (the user may have unsaved work); if it locks the exe, ask the user to close it.
- Keep the `Co-Authored-By: Claude` trailer on commits and the AI credit in the README.
