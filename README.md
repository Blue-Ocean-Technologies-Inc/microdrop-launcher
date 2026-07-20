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
| macOS Apple Silicon | [Microdrop-Launcher-macos-arm64.dmg](https://github.com/Blue-Ocean-Technologies-Inc/microdrop-launcher/releases/latest/download/Microdrop-Launcher-macos-arm64.dmg) |
| macOS Intel | [Microdrop-Launcher-macos-x86_64.dmg](https://github.com/Blue-Ocean-Technologies-Inc/microdrop-launcher/releases/latest/download/Microdrop-Launcher-macos-x86_64.dmg) |

The launcher needs only **git** on the machine; it installs pixi itself.

**Linux:** mark the download executable first:
`chmod +x microdrop_setup-linux-x86_64`.

**macOS:** open the dmg and drag **Microdrop Launcher** into Applications. The
app is unsigned, so macOS blocks the first launch — approve it under System
Settings → Privacy & Security → "Open Anyway", or run
`xattr -d com.apple.quarantine "/Applications/Microdrop Launcher.app"`.

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
pip install pillow   # macOS only: converts the .ico for the .app bundle
pyinstaller --clean --noconfirm microdrop_setup.spec
# -> dist/microdrop_setup.exe (Windows), dist/microdrop_setup (Linux),
#    dist/"Microdrop Launcher.app" (macOS; CI wraps it in a dmg)
```

Releases are fully automated: on every push to `main`,
`.github/workflows/release.yml` runs `cz bump` (commitizen, `.cz.toml`) to
derive the next semver from Conventional Commits — `fix:` → patch, `feat:` →
minor, `BREAKING CHANGE` → major — commit the `CHANGELOG.md` update, tag
`vX.Y.Z`, build all four platform binaries, and publish a GitHub Release with
the changelog as notes. Pushes containing only non-releasable commits
(`docs:`/`chore:`/`ci:`…) don't release. Manual `workflow_dispatch` runs build
artifacts only.
