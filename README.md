# Microdrop Launcher

Standalone setup & launcher for [Microdrop](https://github.com/Blue-Ocean-Technologies-Inc/Microdrop)
(the Sci-Bots digital-microfluidics control system). It is the bootstrap a new
user runs **before** any project environment exists, so it lives in its own repo
and ships as a single-file binary for Windows, Linux, and macOS.

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

## Download

Permanent links — these always point at the newest release:

| OS | Download |
|---|---|
| Windows x64 | [microdrop_setup.exe](https://github.com/Blue-Ocean-Technologies-Inc/microdrop-launcher/releases/latest/download/microdrop_setup.exe) |
| Linux x64 | [microdrop_setup-linux-x86_64](https://github.com/Blue-Ocean-Technologies-Inc/microdrop-launcher/releases/latest/download/microdrop_setup-linux-x86_64) |
| macOS Apple Silicon | [microdrop_setup-macos-arm64](https://github.com/Blue-Ocean-Technologies-Inc/microdrop-launcher/releases/latest/download/microdrop_setup-macos-arm64) |
| macOS Intel | [microdrop_setup-macos-x86_64](https://github.com/Blue-Ocean-Technologies-Inc/microdrop-launcher/releases/latest/download/microdrop_setup-macos-x86_64) |

The binaries need only **git** on the machine; the launcher installs pixi
itself. On Linux/macOS, mark the download executable first:
`chmod +x microdrop_setup-*`. The macOS binaries are unsigned, so Gatekeeper
quarantines them on first run; clear it with
`xattr -d com.apple.quarantine microdrop_setup-macos-*` (or right-click → Open
once).

## Usage

```bash
# GUI (setup + launcher)
python microdrop_setup.py

# Headless launch of a saved config (what desktop shortcuts run)
python microdrop_setup.py --launch [--profile <name>]
```

## How it finds the install

The launcher is location-independent. It stores the chosen install directory in
its config and resolves everything (repo tree, settings files, icons, the
`launch_microdrop.*` scripts) against it. At launch it invokes the bundled
`launch_microdrop.ps1` / `.sh` and passes the install dir explicitly
(`-InstallDir` / `--install-dir`), so it does not need to live inside the
`pixi-microdrop` checkout.

## Building locally

```bash
pip install "pyinstaller>=6,<7"
pyinstaller --clean --noconfirm microdrop_setup.spec
# -> dist/microdrop_setup.exe (Windows) or dist/microdrop_setup (Linux/macOS)
```

Releases are fully automated: on every push to `main`,
`.github/workflows/release.yml` runs `cz bump` (commitizen, `.cz.toml`) to
derive the next semver from Conventional Commits — `fix:` → patch, `feat:` →
minor, `BREAKING CHANGE` → major — commit the `CHANGELOG.md` update, tag
`vX.Y.Z`, build all four platform binaries, and publish a GitHub Release with
the changelog as notes. Pushes containing only non-releasable commits
(`docs:`/`chore:`/`ci:`…) don't release. Manual `workflow_dispatch` runs build
artifacts only.
