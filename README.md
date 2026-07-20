# Microdrop Launcher

Standalone setup & launcher for [Microdrop](https://github.com/Blue-Ocean-Technologies-Inc/Microdrop)
(the Sci-Bots digital-microfluidics control system). It is the bootstrap a new
user runs **before** any project environment exists, so it lives in its own repo
and ships as a single Windows `.exe`.

`microdrop_setup.py` is **Python stdlib only** (tkinter GUI) — it must run before
pixi or the project env are installed.

## What it does

**Stage 1 — pre-install:** installs [pixi](https://pixi.prefix.dev) if missing,
clones [`pixi-microdrop`](https://github.com/Blue-Ocean-Technologies-Inc/pixi-microdrop)
(with the Microdrop source submodule) into a chosen install directory, and
prefetches the environment.

**Stage 2 — launcher:** a tabbed GUI to pick the launch **mode**
(frontend / backend / dual), **device** (dropbot / opendrop / mock), and
per-group plugins; manage repo branches and git maintenance (pull / stash /
reset); and edit server settings (Redis host/port, Dramatiq worker
threads/timeout). It can save named **config profiles** and create desktop
shortcuts, each launching its own profile via `--launch --profile <name>`.

## Usage

```bash
# GUI (setup + launcher)
python microdrop_setup.py

# Headless launch of a saved config (what desktop shortcuts run)
python microdrop_setup.py --launch [--profile <name>]
```

The prebuilt `microdrop_setup.exe` (see Releases) needs only **git** on the
machine; it installs pixi itself.

## How it finds the install

The launcher is location-independent. It stores the chosen install directory in
its config and resolves everything (repo tree, settings files, icons, the
`launch_microdrop.*` scripts) against it. At launch it invokes the bundled
`launch_microdrop.ps1` / `.sh` and passes the install dir explicitly
(`-InstallDir` / `--install-dir`), so it does not need to live inside the
`pixi-microdrop` checkout.

## Building the exe locally

```bash
pip install "pyinstaller>=6,<7"
pyinstaller --clean --noconfirm microdrop_setup.spec
# -> dist/microdrop_setup.exe
```

CI (`.github/workflows/release.yml`) builds the exe on every `v*` tag and
attaches it to the matching GitHub Release. Versioning/changelog follow
Conventional Commits via commitizen (`.cz.toml`).
