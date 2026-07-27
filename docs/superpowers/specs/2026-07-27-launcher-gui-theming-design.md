# Modernized launcher GUI: Sun Valley theme + layout polish

Date: 2026-07-27
Status: approved, ready for implementation planning

## Goal

Make the `microdrop_setup.py` tkinter GUI look like a current desktop
application instead of a stock Tk form dump, with real light/dark support that
follows the user's OS preference.

The launcher runs *before* pixi or any project environment exists, so it cannot
grow pip dependencies. The theme is therefore vendored into the repo as Tcl and
PNG assets and loaded directly, not installed.

## Reference

The stated model was [GlycoGenius_GUI](https://github.com/LoponteHF/GlycoGenius_GUI).
Worth recording what that project actually does, because it is not what the
name "themed tkinter" suggests: its `requirements.txt` contains no theme
library (no `ttkbootstrap`, no `sv-ttk`, no Azure/Forest), and `GUI.py` never
calls `theme_use`. It runs the **native** OS theme and gets its polish from
about fifteen named `ttk.Style()` entries, consistent Segoe UI sizing, generous
button padding, titled `LabelFrame` panels, PNG icon buttons, and a branded
header strip.

We deliberately went further than the reference: this design adopts a genuine
flat theme with dark mode, which GlycoGenius does not have. The GlycoGenius
influence that survives is structural — the header band, the grouping into
titled cards, and the typography/padding discipline.

## Scope

In scope:

- Vendored Sun Valley ttk theme, light and dark.
- Theme mode following the OS, overridable from the Options menu, persisted.
- A `microdrop_theme.py` module owning all presentation concerns.
- Header band with icon, title, version, and repo checkout status.
- Regrouping of the Launch tab's mode/device rows into titled cards.
- Button hierarchy: accent primary action, default secondary actions.
- Correct colors for the non-ttk widgets (`tk.Text`, `tk.Canvas`).
- A window/taskbar icon, which the launcher currently never sets.

Out of scope:

- Navigation changes. The notebook, its three tabs, and the wizard flow stay
  exactly as they are.
- Windows DPI awareness. See "Rejected" below.
- Any change to install, git, config, or launch behaviour.

## Architecture

### Theme delivery

Vendor the Tcl and sprite assets only, not `sv_ttk`'s Python wrapper. The
wrapper resolves its theme with `Path(__file__).with_name("sv.tcl")`, which
under PyInstaller onefile depends on getting a bundled-package layout right.
`microdrop_setup.py` already solves this problem for `launch_microdrop.ps1` via
`launcher_assets_dir()`, which reads from `sys._MEIPASS` when frozen. Reuse it.

```
assets/
  sv_ttk/                     # vendored from rdbende/Sun-Valley-ttk-theme, MIT
    sv.tcl
    theme/
      light.tcl   dark.tcl
      sprites_light.tcl   sprites_dark.tcl
      spritesheet_light.png   spritesheet_dark.png
  microdrop_icon.png          # header + window icon
LICENSE-sun-valley            # MIT attribution, required by the licence
```

Seven files, roughly 80 KB.

**The `theme/` subdirectory is load-bearing and must not be flattened.**
`sv.tcl:3-4` sources `[file join [file dirname [info script]] theme light.tcl]`,
`light.tcl:1` sources `sprites_light.tcl` from its own directory, and
`light.tcl:24` loads `spritesheet_light.png` the same way. Mirroring the
upstream layout exactly means the vendored files need no edits, which in turn
keeps re-vendoring a newer upstream release a matter of copying files over.
That is a requirement, not a convenience.

Loading:

```python
root.tk.call("source", str(launcher_assets_dir() / "sv_ttk" / "sv.tcl"))
ttk.Style(root).theme_use("sun-valley-dark")
```

`microdrop_setup.spec` gains a `datas` entry for `assets/`.

### Module boundary

New file `microdrop_theme.py`, roughly 150 lines, is the only place that knows
about colors, fonts, padding, or the theme library.

| Function | Responsibility |
|---|---|
| `apply(root, mode)` | Resolve mode, source the Tcl, `theme_use`, register named styles, recolor registered plain widgets. Idempotent. |
| `resolve_mode(mode)` | `"system"` → `"light"`/`"dark"` via OS detection; passes `"light"`/`"dark"` through. |
| `register_plain_widget(widget, role)` | Track a non-ttk widget so it is recolored on every `apply()`. Roles: `"log"`, `"surface"`. |
| `tokens(mode)` | The active color table, for callers that need a raw value. |

`microdrop_setup.py` imports it **inside** the GUI constructors, never at module
scope. See Risk 1.

### Tokens

```python
TOKENS = {
    "dark":  {"bg": "#1c1c1c", "surface": "#202020", "border": "#2d2d2d",
              "text": "#ffffff", "muted": "#9a9a9a",
              "log_bg": "#191919", "log_fg": "#d8d8d8"},
    "light": {"bg": "#fafafa", "surface": "#ffffff", "border": "#e5e5e5",
              "text": "#1a1a1a", "muted": "#606060",
              "log_bg": "#ffffff", "log_fg": "#1a1a1a"},
}
PAD = {"xs": 2, "sm": 4, "md": 8, "lg": 12, "xl": 16}
```

Named styles: `Header.TLabel`, `Muted.TLabel`, `Card.TFrame`, `Toolbutton` for
collapsible headers. `Accent.TButton` is supplied by Sun Valley itself.

### Fonts

`sv.tcl` requests "Segoe UI Variable", which ships on Windows 11 only. Windows
10, Linux, and macOS fall back to whatever Tk picks. `microdrop_theme.py` sets
an explicit fallback family so the fallback is chosen rather than arbitrary.

## Changes to existing code

Every row below is a real location in the current `microdrop_setup.py`.

| # | Location | Problem | Fix |
|---|---|---|---|
| 1 | `:660` `tk.Text` log pane | Not ttk; stays white bg, black text in dark mode | Set `bg`/`fg`/`insertbackground` from tokens; register as role `"log"` |
| 2 | `:727` `tk.Canvas` scroll region | Defaults white; shows as a white gutter behind the plugin list | Set `bg` to `surface`; register as role `"surface"` |
| 3 | `:1010`, `:1016` | Hardcoded `foreground="gray40"`, unreadable on `#1c1c1c` | Replace both with `Muted.TLabel` |
| 4 | `:762` `relief="groove", borderwidth=1` | Bevelled 3D border, wrong under a flat theme | `Card.TFrame`, flat 1px `border` token |
| 5 | `:979-985` `tk.Menu` menubar | Unthemed on Windows and macOS | Accepted limitation, see below |
| 6 | `:962` `geometry("900x780")` | Sun Valley widgets are taller; content clips | Re-measure and raise; keep `minsize` proportional |
| 7 | `:549` update-notification bar | Plain frame, reads as a stray row | `Card.TFrame` plus accent Download button |
| 8 | `:990-995` action buttons | No visual hierarchy | `Accent.TButton` on Launch; others unchanged |
| 9 | `:1033-1049` mode and device rows | Bare rows, inconsistent with the plugin groups below | Two `Card.TFrame` sections with headings |
| 10 | `:998-1016` profile and version rows | Unstructured | Replaced by the header band |

Items 1 and 2 are what make an otherwise-correct dark theme look broken;
`register_plain_widget()` exists so they stay in sync rather than depending on
each call site remembering to recolor.

Item 5 is a genuine upstream constraint, not an oversight: `sv.tcl`'s
`config_menus` proc returns early when the windowing system is `win32` or
`aqua`, so only Linux/X11 menubars get themed colors. Windows and macOS draw
menubars natively.

### Header band

Replaces the current profile and version rows.

```
+----------------------------------------------------------+
|  [icon]  Microdrop Launcher                       v0.5.0  |
|          pixi-microdrop: main@a1b2c3   source: dev@d4e5f6 |
+----------------------------------------------------------+
|  Profile: [ (default)      v ]   shortcut exists          |
+----------------------------------------------------------+
```

The icon requires a vendored `assets/microdrop_icon.png`, because Tk's
`PhotoImage` reads PNG and GIF but not ICO, and `ICON_PNG_RELPATH`
(`microdrop_setup.py:41`) points inside the *installed* repo, which does not
exist yet during the wizard. The same asset is used for `root.iconphoto()`,
giving the launcher a window and taskbar icon it currently lacks.

`launcher_version()` returns `None` on non-frozen runs, so the version badge
falls back to `dev`.

## Theme mode

New config key `"theme"`, default `"system"`, values `"system" | "light" | "dark"`.
An Options-menu radio group sits beside the existing Advanced-mode item and
persists the choice.

Detection is stdlib only:

| OS | Source | On failure |
|---|---|---|
| Windows | `winreg`, `…\Themes\Personalize\AppsUseLightTheme` | light |
| macOS | `subprocess`, `defaults read -g AppleInterfaceStyle` | light (non-zero exit means light) |
| Linux | `subprocess`, `gsettings get org.gnome.desktop.interface color-scheme` | light |

Every branch is wrapped so detection failure degrades to light rather than
raising. This code runs before anything is installed, on machines we do not
control.

Unknown or malformed values of the `"theme"` config key resolve to `"system"`,
so a hand-edited or older config file never prevents the GUI from starting.

## Risks

### Risk 1 — breaking the headless `--launch` path

`microdrop_setup.py:650` documents that tkinter imports stay function-local so
`--launch` works without Tk, and desktop shortcuts run exactly that path.
`microdrop_theme.py` imports tkinter at its top level.

**Therefore `microdrop_setup.py` must import `microdrop_theme` inside the GUI
constructors, never at module scope.** A top-level import would make every
desktop shortcut fail on a headless or Tk-less machine, and would pass every
local check on a developer machine that has Tk.

### Risk 2 — Tk resets named styles on `theme_use()`

Each ttk theme carries its own style database. A `style.configure("Muted.TLabel", …)`
registered while `sun-valley-light` is active does not survive a switch to
`sun-valley-dark`. `apply()` must therefore re-register every named style
*after* each `theme_use()` call, which is why it is specified as idempotent.
Getting this wrong presents as "styles work until you toggle the theme once".

### Risk 3 — frozen build cannot find the theme

Only reproducible against a real PyInstaller build, never against a source run.

### Rollback

Setting `"theme": "light"` is not an escape hatch if theming itself misbehaves.
`apply()` catches a failed `source` or `theme_use` and returns silently, leaving
the stock native theme in place. A broken theme must never stop someone
installing Microdrop.

## Verification

The repo has no test suite and CI covers only conventional commits and release,
so verification is a smoke script plus a manual pass.

Automated:

```
py_compile microdrop_setup.py microdrop_theme.py
--launch with tkinter blocked from sys.modules, assert it still runs   # Risk 1
apply() -> toggle -> toggle, assert Muted.TLabel foreground still
  matches the token for the active mode                               # Risk 2
pyinstaller microdrop_setup.spec, run the resulting exe               # Risk 3
```

Manual, for each of light and dark:

- Wizard, including the log pane during a real install
- All three tabs
- Collapsible plugin groups, expanded and collapsed
- Scrolled plugin list, checking for a white gutter
- Update-notification bar
- Profile switching

## Rejected

**Windows DPI awareness** (`SetProcessDpiAwareness`). It would sharpen text, but
Sun Valley's controls are bitmap spritesheets that do not scale. At 150% the
result is crisp text inside soft, undersized widgets, which reads worse than
uniform softness. Revisit only if HiDPI complaints arrive, as its own change.

**Forest and Azure themes.** Comparable size and quality, but less active
(Azure was last touched in 2023). Sun Valley is the Windows 11 Fluent look,
which suits a Windows-primary user base, and was last updated 2025-06.

**Vendoring `sv_ttk`'s Python wrapper.** Adds a `__file__`-relative path
resolution problem under PyInstaller that `launcher_assets_dir()` already
solves.

**Navigation redesign** (a GlycoGenius-style `Install > Configure > Launch`
workflow strip). The largest visual payoff, but it touches navigation and state
flow, and this change is meant to be visual. Possible as a later change.
