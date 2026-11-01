# Grandmist roadmap

Grandmist is a **chess visualization** toolkit: see the shape of your games and repertoire, and see what the engine sees.

Status legend: ✅ done · 🔜 next · 🧪 later

## Visualization
- ✅ Tree view of a record or a whole `.gm` file, variations included
- 🔜 Engine-coloured tree: colour each node by evaluation, mark the moves where the evaluation swings
- 🔜 Branch comparison: pick two branches and compare their evaluation curves and resulting positions side by side
- 🔜 Player overview for imported games: opening tree with results per colour, progress over time

## Engines
Grandmist hosts any UCI engine (Lc0, Stockfish, …) as a separate program and talks to it over the UCI text protocol.
- ✅ Load UCI engines and switch between them
- ✅ Engine panel: score, win / draw / loss bar, top 3 lines; click a move to play the line
- 🔜 Run two engines at the same time
- 🔜 Optional helper to download Lc0 and a network with the user's consent
- 🧪 Analyse a whole `.gm` file and flag mistakes
- Licensing: Lc0 and Stockfish are GPL-3.0. They stay **separate programs** talking over UCI; their code is never copied into Grandmist. Network files are loaded as separate files.

## Files and import
- ✅ `.gm` files: one file per collection, New / Open / Save / Save As, double-click to open
- ✅ PGN import / export with variations and comments
- ✅ Import a player's games from Lichess or Chess.com into one `.gm`
- ✅ English, Chinese and Russian; more languages via `lang/xx.json`
