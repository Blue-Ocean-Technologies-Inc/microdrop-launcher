# Launcher GUI Theming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give `microdrop_setup.py` a modern flat look with real light/dark support that follows the OS preference, without adding any pip dependency.

**Architecture:** The Sun Valley ttk theme is vendored into `assets/sv_ttk/` as Tcl and PNG files and sourced directly through the existing `launcher_assets_dir()` helper, which already resolves `sys._MEIPASS` for frozen builds. A new `microdrop_theme.py` module owns every presentation concern — color tokens, named ttk styles, OS theme detection, and recoloring of the two non-ttk widgets. `microdrop_setup.py` calls into it and otherwise keeps its existing structure.

**Tech Stack:** Python 3 stdlib only (`tkinter`, `ttk`, `winreg`, `subprocess`, `unittest`), Tcl/Tk 8.6+, PyInstaller for the frozen build. Pillow is used once at development time to generate an icon asset; it is not a runtime dependency.

**Spec:** `docs/superpowers/specs/2026-07-27-launcher-gui-theming-design.md`

## Global Constraints

These apply to every task. Violating any one of them is a defect regardless of whether the task's own tests pass.

- **No pip dependencies may be added to the runtime.** `microdrop_setup.py` and `microdrop_theme.py` import stdlib only. This is why the theme is vendored rather than installed.
- **`microdrop_setup.py` must never import `microdrop_theme` at module scope.** `microdrop_theme` imports `tkinter` at its top level, and `microdrop_setup.py:650` documents that tkinter imports stay function-local so `--launch` works without Tk. Desktop shortcuts run that path. Import inside GUI functions and constructors only.
- **Vendored files under `assets/sv_ttk/` must not be edited.** Re-vendoring a newer upstream release must stay a copy-over operation.
- **The `assets/sv_ttk/theme/` subdirectory is load-bearing.** `sv.tcl:3-4` sources `theme/light.tcl`; `light.tcl:1` and `light.tcl:24` load `sprites_light.tcl` and `spritesheet_light.png` from their own directory. Do not flatten.
- **Theme failure must never block installing Microdrop.** `apply()` catches its own exceptions and leaves the stock native theme in place.
- **Tcl/Tk 8.6 minimum** — `sv.tcl:1` is `package require Tk 8.6-`.
- Commit messages follow Conventional Commits (`.cz.toml`, enforced by `.github/workflows/conventional-commits.yml`).
- Tests use stdlib `unittest`, run via `python -m unittest`. The repo has no pytest and must not gain one.

## File Structure

| File | Responsibility |
|---|---|
| `assets/sv_ttk/**` | Vendored Sun Valley theme. Never edited. |
| `assets/microdrop_icon.png` | 64x64 header and window icon, generated from `Microdrop_Icon.ico`. |
| `LICENSE-sun-valley` | MIT attribution for the vendored theme. |
| `microdrop_theme.py` | **New.** Tokens, named styles, OS detection, `apply()`, plain-widget registry. The only file that knows a color literal. |
| `microdrop_setup.py` | Modified. Calls `microdrop_theme`, adds the header band and the theme menu, drops hardcoded colors and reliefs. |
| `microdrop_setup.spec` | Modified. Ships `assets/` in `datas`. |
| `tests/test_theme.py` | **New.** Unit tests for `microdrop_theme`. |
| `tests/test_headless.py` | **New.** Guards the `--launch` path against a tkinter import regression. |

---

### Task 1: Vendor the theme assets and ship them in the build

**Files:**
- Create: `assets/sv_ttk/sv.tcl`, `assets/sv_ttk/theme/{light,dark,sprites_light,sprites_dark}.tcl`, `assets/sv_ttk/theme/spritesheet_{light,dark}.png`
- Create: `LICENSE-sun-valley`
- Create: `tests/__init__.py`, `tests/test_assets.py`
- Modify: `microdrop_setup.spec:28-32` (the `datas` list)

**Interfaces:**
- Consumes: nothing.
- Produces: the on-disk layout `assets/sv_ttk/sv.tcl` and `assets/sv_ttk/theme/`, which Task 3's `apply()` resolves via `launcher_assets_dir() / "assets" / "sv_ttk" / "sv.tcl"`.

- [ ] **Step 1: Download the vendored theme files**

```bash
cd "C:/Users/Info/PycharmProjects/microdrop-launcher"
mkdir -p assets/sv_ttk/theme
BASE=https://raw.githubusercontent.com/rdbende/Sun-Valley-ttk-theme/main/sv_ttk
curl -sL "$BASE/sv.tcl" -o assets/sv_ttk/sv.tcl
for f in light.tcl dark.tcl sprites_light.tcl sprites_dark.tcl \
         spritesheet_light.png spritesheet_dark.png; do
  curl -sL "$BASE/theme/$f" -o "assets/sv_ttk/theme/$f"
done
curl -sL https://raw.githubusercontent.com/rdbende/Sun-Valley-ttk-theme/main/LICENSE \
  -o LICENSE-sun-valley
```

- [ ] **Step 2: Write the failing test**

Create `tests/__init__.py` as an empty file, then create `tests/test_assets.py`:

```python
"""The vendored theme must keep upstream's directory layout.

sv.tcl sources theme/light.tcl by relative path, which in turn loads
sprites_light.tcl and spritesheet_light.png from its own directory. A
flattened or partial vendoring fails only at runtime, inside Tcl, with an
error that does not name the missing file clearly — so assert it here.
"""
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
THEME_DIR = REPO_ROOT / "assets" / "sv_ttk"

EXPECTED = (
    "sv.tcl",
    "theme/light.tcl",
    "theme/dark.tcl",
    "theme/sprites_light.tcl",
    "theme/sprites_dark.tcl",
    "theme/spritesheet_light.png",
    "theme/spritesheet_dark.png",
)


class TestVendoredTheme(unittest.TestCase):
    def test_all_expected_files_present(self):
        missing = [name for name in EXPECTED
                   if not (THEME_DIR / name).is_file()]
        self.assertEqual([], missing)

    def test_sv_tcl_sources_theme_subdirectory(self):
        # Guards against someone "tidying" the tree into a flat directory.
        text = (THEME_DIR / "sv.tcl").read_text(encoding="utf-8")
        self.assertIn("theme light.tcl", text)

    def test_licence_is_vendored(self):
        licence = (REPO_ROOT / "LICENSE-sun-valley").read_text(encoding="utf-8")
        self.assertIn("MIT", licence)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the test**

Run: `python -m unittest tests.test_assets -v`
Expected: PASS, since Step 1 already placed the files. If it fails, Step 1's download did not complete — do not proceed.

- [ ] **Step 4: Ship the assets in the frozen build**

In `microdrop_setup.spec`, the `datas` list currently reads:

```python
    datas=[
        ('launch_microdrop.ps1', '.'),
        ('launch_microdrop.sh', '.'),
        (_version_file, '.'),
    ],
```

Change it to:

```python
    datas=[
        ('launch_microdrop.ps1', '.'),
        ('launch_microdrop.sh', '.'),
        (_version_file, '.'),
        # Vendored Sun Valley ttk theme + icon. The whole tree is copied so
        # sv.tcl still finds theme/light.tcl at the relative path it expects.
        ('assets', 'assets'),
    ],
```

- [ ] **Step 5: Commit**

```bash
git add assets LICENSE-sun-valley tests microdrop_setup.spec
git commit -m "feat: vendor the Sun Valley ttk theme assets"
```

---

### Task 2: Theme mode resolution and color tokens

Pure logic, no Tk. This is the half of `microdrop_theme.py` that is fully testable without a display.

**Files:**
- Create: `microdrop_theme.py`
- Create: `tests/test_theme.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `TOKENS: dict[str, dict[str, str]]` keyed `"light"` / `"dark"`.
  - `PAD: dict[str, int]` keyed `"xs" "sm" "md" "lg" "xl"`.
  - `resolve_mode(mode: str | None) -> str` returning exactly `"light"` or `"dark"`.
  - `tokens(mode: str | None) -> dict[str, str]`.
  - `_os_prefers_dark() -> bool` — dispatches per platform, never raises.

- [ ] **Step 1: Write the failing test**

Create `tests/test_theme.py`:

```python
"""Tests for the parts of microdrop_theme that need no display."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import microdrop_theme  # noqa: E402


class TestResolveMode(unittest.TestCase):
    def test_explicit_modes_pass_through(self):
        self.assertEqual("light", microdrop_theme.resolve_mode("light"))
        self.assertEqual("dark", microdrop_theme.resolve_mode("dark"))

    def test_system_follows_os_preference(self):
        original = microdrop_theme._os_prefers_dark
        try:
            microdrop_theme._os_prefers_dark = lambda: True
            self.assertEqual("dark", microdrop_theme.resolve_mode("system"))
            microdrop_theme._os_prefers_dark = lambda: False
            self.assertEqual("light", microdrop_theme.resolve_mode("system"))
        finally:
            microdrop_theme._os_prefers_dark = original

    def test_unknown_values_are_treated_as_system(self):
        # A hand-edited or older config must never stop the GUI starting.
        original = microdrop_theme._os_prefers_dark
        try:
            microdrop_theme._os_prefers_dark = lambda: True
            for value in (None, "", "midnight", "DARK MODE", 7):
                self.assertEqual("dark", microdrop_theme.resolve_mode(value))
        finally:
            microdrop_theme._os_prefers_dark = original

    def test_detection_failure_falls_back_to_light(self):
        original = microdrop_theme._detectors
        try:
            def boom():
                raise OSError("no registry here")
            microdrop_theme._detectors = {"nt": boom}
            self.assertFalse(microdrop_theme._os_prefers_dark())
        finally:
            microdrop_theme._detectors = original


class TestTokens(unittest.TestCase):
    def test_both_modes_define_the_same_keys(self):
        self.assertEqual(set(microdrop_theme.TOKENS["light"]),
                         set(microdrop_theme.TOKENS["dark"]))

    def test_tokens_resolves_mode(self):
        self.assertEqual(microdrop_theme.TOKENS["dark"],
                         microdrop_theme.tokens("dark"))

    def test_every_token_is_a_hex_colour(self):
        for mode, table in microdrop_theme.TOKENS.items():
            for name, value in table.items():
                with self.subTest(mode=mode, token=name):
                    self.assertRegex(value, r"^#[0-9a-fA-F]{6}$")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest tests.test_theme -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'microdrop_theme'`

- [ ] **Step 3: Write the implementation**

Create `microdrop_theme.py`:

```python
"""Presentation layer for the Microdrop launcher GUI.

Everything the launcher knows about colour, typography, spacing, and the
vendored Sun Valley ttk theme lives here. microdrop_setup.py imports this
module *inside* its GUI functions — never at module scope — because this
module imports tkinter and the headless --launch path must keep working on
machines without Tk.
"""
import os
import subprocess
import sys

# Colour tokens. Kept as a table rather than scattered literals so a theme
# switch is a dict lookup and the tests can assert both modes stay in sync.
TOKENS = {
    "dark": {
        "bg": "#1c1c1c",
        "surface": "#202020",
        "border": "#2d2d2d",
        "text": "#ffffff",
        "muted": "#9a9a9a",
        "warn": "#ff7b72",
        "log_bg": "#191919",
        "log_fg": "#d8d8d8",
    },
    "light": {
        "bg": "#fafafa",
        "surface": "#ffffff",
        "border": "#e5e5e5",
        "text": "#1a1a1a",
        "muted": "#606060",
        "warn": "#b00020",
        "log_bg": "#ffffff",
        "log_fg": "#1a1a1a",
    },
}

# One spacing scale, in pixels, so padding stays on a rhythm.
PAD = {"xs": 2, "sm": 4, "md": 8, "lg": 12, "xl": 16}

# Config values accepted for the "theme" key.
MODES = ("system", "light", "dark")


def _windows_prefers_dark():
    import winreg
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
    try:
        apps_use_light, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
    finally:
        winreg.CloseKey(key)
    return not apps_use_light


def _macos_prefers_dark():
    # Returns non-zero when the key is unset, which is exactly the light case.
    result = subprocess.run(
        ["defaults", "read", "-g", "AppleInterfaceStyle"],
        capture_output=True, text=True, timeout=5)
    return result.stdout.strip().lower() == "dark"


def _linux_prefers_dark():
    result = subprocess.run(
        ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
        capture_output=True, text=True, timeout=5)
    return "dark" in result.stdout.strip().lower()


# Keyed by os.name so a test can swap the whole table out.
_detectors = {
    "nt": _windows_prefers_dark,
    "posix": _macos_prefers_dark if sys.platform == "darwin"
    else _linux_prefers_dark,
}


def _os_prefers_dark():
    """True when the desktop is set to dark. Light on anything unexpected.

    This runs before Microdrop is installed, on machines we do not control:
    a missing registry key, no gsettings binary, or a sandboxed subprocess
    must degrade to a readable light theme rather than raise.
    """
    detector = _detectors.get(os.name)
    if detector is None:
        return False
    try:
        return bool(detector())
    except Exception:
        return False


def resolve_mode(mode):
    """Map a config value to the concrete theme to load.

    Anything that is not exactly "light" or "dark" — including None, a typo,
    or a value written by a future version — is treated as "system".
    """
    if mode in ("light", "dark"):
        return mode
    return "dark" if _os_prefers_dark() else "light"


def tokens(mode):
    """Colour table for *mode*, resolving "system" first."""
    return TOKENS[resolve_mode(mode)]
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m unittest tests.test_theme -v`
Expected: PASS, 7 tests.

- [ ] **Step 5: Commit**

```bash
git add microdrop_theme.py tests/test_theme.py
git commit -m "feat: add theme mode resolution and colour tokens"
```

---

### Task 3: Load the theme and register named styles

Adds the Tk-dependent half of `microdrop_theme.py`. Note Risk 2 from the spec: ttk keeps a **separate style database per theme**, so named styles configured under `sun-valley-light` do not survive a switch to `sun-valley-dark`. `apply()` therefore re-registers every style after each `theme_use()`, and the test asserts exactly that.

**Files:**
- Modify: `microdrop_theme.py`
- Modify: `tests/test_theme.py`

**Interfaces:**
- Consumes: `resolve_mode`, `tokens`, `TOKENS`, `PAD` from Task 2.
- Produces:
  - `theme_dir() -> pathlib.Path` — directory holding `sv.tcl`.
  - `apply(root, mode) -> str` — returns the mode actually applied (`"light"`/`"dark"`), or `"native"` when theming failed and the stock theme was left alone. Idempotent; safe to call repeatedly on the same root.
  - Named styles registered by `apply()`: `Header.TLabel`, `Muted.TLabel`, `Warn.TLabel`, `Card.TFrame`, `CardTitle.TLabel`. `Accent.TButton` comes from Sun Valley itself.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_theme.py`, above the `if __name__` block:

```python
def _make_root():
    """A hidden Tk root, or None when no display is available."""
    try:
        import tkinter as tk
    except ImportError:
        return None
    try:
        root = tk.Tk()
    except Exception:
        return None
    root.withdraw()
    return root


class TestApply(unittest.TestCase):
    def setUp(self):
        self.root = _make_root()
        if self.root is None:
            self.skipTest("no display available")

    def tearDown(self):
        if self.root is not None:
            self.root.destroy()

    def test_apply_returns_the_mode_it_loaded(self):
        self.assertEqual("dark", microdrop_theme.apply(self.root, "dark"))
        self.assertEqual("light", microdrop_theme.apply(self.root, "light"))

    def test_apply_selects_the_sun_valley_theme(self):
        from tkinter import ttk
        microdrop_theme.apply(self.root, "dark")
        self.assertEqual("sun-valley-dark", ttk.Style(self.root).theme_use())

    def test_named_styles_survive_a_theme_switch(self):
        # Risk 2: ttk keeps a style database per theme, so styles registered
        # under one theme vanish when another is selected. apply() must
        # re-register them every time, not once at startup.
        from tkinter import ttk
        style = ttk.Style(self.root)
        for mode in ("dark", "light", "dark", "light"):
            microdrop_theme.apply(self.root, mode)
            expected = microdrop_theme.TOKENS[mode]["muted"]
            actual = style.lookup("Muted.TLabel", "foreground")
            self.assertEqual(expected, actual, f"lost after switching to {mode}")

    def test_apply_is_idempotent(self):
        from tkinter import ttk
        for _ in range(3):
            microdrop_theme.apply(self.root, "dark")
        self.assertEqual("sun-valley-dark", ttk.Style(self.root).theme_use())

    def test_theming_failure_leaves_the_native_theme(self):
        # A broken or missing theme must never stop someone installing
        # Microdrop, so apply() swallows its own errors.
        from tkinter import ttk
        original = microdrop_theme.theme_dir
        before = ttk.Style(self.root).theme_use()
        try:
            microdrop_theme.theme_dir = lambda: Path("/nonexistent/theme/dir")
            self.assertEqual("native", microdrop_theme.apply(self.root, "dark"))
        finally:
            microdrop_theme.theme_dir = original
        self.assertEqual(before, ttk.Style(self.root).theme_use())
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest tests.test_theme -v`
Expected: FAIL with `AttributeError: module 'microdrop_theme' has no attribute 'apply'`

- [ ] **Step 3: Write the implementation**

Append to `microdrop_theme.py`:

```python
def theme_dir():
    """Directory holding the vendored sv.tcl.

    Mirrors microdrop_setup.launcher_assets_dir(): a frozen build reads from
    the PyInstaller bundle, a plain script run from the repo checkout. Kept
    independent of microdrop_setup so this module stays importable alone.
    """
    from pathlib import Path
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS",
                            Path(sys.executable).resolve().parent))
    else:
        base = Path(__file__).resolve().parent
    return base / "assets" / "sv_ttk"


def _register_styles(style, mode):
    """(Re-)register every named style against the active ttk theme.

    Must run after each theme_use(): ttk stores styles per theme, so what was
    configured under sun-valley-light is simply absent under sun-valley-dark.
    """
    palette = TOKENS[mode]
    style.configure("Header.TLabel",
                    font=("Segoe UI", 16, "bold"), foreground=palette["text"])
    style.configure("Muted.TLabel", foreground=palette["muted"])
    style.configure("Warn.TLabel", foreground=palette["warn"])
    style.configure("CardTitle.TLabel",
                    font=("Segoe UI", 10, "bold"), foreground=palette["text"])
    style.configure("Card.TFrame",
                    background=palette["surface"],
                    relief="solid", borderwidth=1,
                    bordercolor=palette["border"])


def apply(root, mode):
    """Load the vendored theme onto *root* and register the named styles.

    Returns the mode actually applied — "light" or "dark" — or "native" if
    anything went wrong, in which case the stock ttk theme is left untouched.
    Safe to call repeatedly; sourcing sv.tcl twice is a no-op in Tcl.
    """
    from tkinter import ttk
    resolved = resolve_mode(mode)
    style = ttk.Style(root)
    try:
        if not getattr(root, "_sv_tcl_sourced", False):
            root.tk.call("source", str(theme_dir() / "sv.tcl"))
            root._sv_tcl_sourced = True
        style.theme_use(f"sun-valley-{resolved}")
    except Exception:
        # Deliberately broad: a missing asset, an unsupported Tk, or a Tcl
        # parse error must all degrade to "app still works, looks stock".
        return "native"

    _register_styles(style, resolved)
    root.configure(background=TOKENS[resolved]["bg"])
    _recolour_registered(resolved)
    return resolved
```

Also add the placeholder the last line depends on — Task 4 fills it in. Put it just above `apply`:

```python
def _recolour_registered(mode):
    """No-op until Task 4 adds the plain-widget registry."""
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m unittest tests.test_theme -v`
Expected: PASS. On a machine with no display the five `TestApply` tests report as skipped, which is acceptable — but on the Windows development machine they must actually run and pass.

- [ ] **Step 5: Commit**

```bash
git add microdrop_theme.py tests/test_theme.py
git commit -m "feat: load the vendored theme and register named styles"
```

---

### Task 4: Recolour the non-ttk widgets

`tk.Text` and `tk.Canvas` are not ttk widgets, so no theme touches them. Left alone they stay white in dark mode, which is what makes an otherwise-correct dark theme look broken. A registry keeps them in sync instead of relying on each call site to remember.

**Files:**
- Modify: `microdrop_theme.py`
- Modify: `tests/test_theme.py`

**Interfaces:**
- Consumes: `apply`, `TOKENS` from Task 3.
- Produces: `register_plain_widget(widget, role)` where `role` is `"log"` or `"surface"`. Registration recolours immediately and on every later `apply()`. Dead widgets are dropped silently.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_theme.py`, above the `if __name__` block:

```python
class TestPlainWidgetRegistry(unittest.TestCase):
    def setUp(self):
        self.root = _make_root()
        if self.root is None:
            self.skipTest("no display available")

    def tearDown(self):
        if self.root is not None:
            self.root.destroy()

    def test_registering_recolours_immediately(self):
        import tkinter as tk
        microdrop_theme.apply(self.root, "dark")
        text = tk.Text(self.root)
        microdrop_theme.register_plain_widget(text, "log")
        self.assertEqual(microdrop_theme.TOKENS["dark"]["log_bg"],
                         text.cget("background"))
        self.assertEqual(microdrop_theme.TOKENS["dark"]["log_fg"],
                         text.cget("foreground"))

    def test_registered_widgets_follow_later_switches(self):
        import tkinter as tk
        microdrop_theme.apply(self.root, "dark")
        canvas = tk.Canvas(self.root)
        microdrop_theme.register_plain_widget(canvas, "surface")
        microdrop_theme.apply(self.root, "light")
        self.assertEqual(microdrop_theme.TOKENS["light"]["surface"],
                         canvas.cget("background"))

    def test_destroyed_widgets_are_dropped_not_raised(self):
        import tkinter as tk
        microdrop_theme.apply(self.root, "dark")
        text = tk.Text(self.root)
        microdrop_theme.register_plain_widget(text, "log")
        text.destroy()
        microdrop_theme.apply(self.root, "light")  # must not raise
        self.assertNotIn(text, [w for w, _ in microdrop_theme._plain_widgets])
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest tests.test_theme -v`
Expected: FAIL with `AttributeError: module 'microdrop_theme' has no attribute 'register_plain_widget'`

- [ ] **Step 3: Write the implementation**

In `microdrop_theme.py`, add the registry above `_recolour_registered` and replace that placeholder entirely:

```python
# (widget, role) pairs for non-ttk widgets that no theme reaches.
_plain_widgets = []

# Role -> the tk option names it sets, and the token each reads.
_ROLE_OPTIONS = {
    "log": {"background": "log_bg", "foreground": "log_fg",
            "insertbackground": "log_fg"},
    "surface": {"background": "surface"},
}


def register_plain_widget(widget, role):
    """Track a non-ttk widget so it follows theme switches.

    tk.Text and tk.Canvas ignore ttk themes entirely and would otherwise stay
    white on a dark background. Roles: "log" (text pane) or "surface" (canvas
    or frame backing other widgets).
    """
    _plain_widgets.append((widget, role))
    _apply_role(widget, role, _current_mode or "light")


def _apply_role(widget, role, mode):
    """Set one widget's colours. True if it is still alive."""
    palette = TOKENS[mode]
    try:
        widget.configure(**{option: palette[token]
                            for option, token in _ROLE_OPTIONS[role].items()})
        return True
    except Exception:
        return False  # destroyed, or does not take these options


def _recolour_registered(mode):
    """Recolour every live registered widget; forget the dead ones."""
    _plain_widgets[:] = [(widget, role) for widget, role in _plain_widgets
                         if _apply_role(widget, role, mode)]
```

Add the module-level `_current_mode` near `_plain_widgets`:

```python
# Mode of the most recent successful apply(), for widgets registered later.
_current_mode = None
```

And set it in `apply()`, immediately before the `_recolour_registered(resolved)` call:

```python
    global _current_mode
    _current_mode = resolved
    _recolour_registered(resolved)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m unittest tests.test_theme -v`
Expected: PASS, all tests.

- [ ] **Step 5: Commit**

```bash
git add microdrop_theme.py tests/test_theme.py
git commit -m "feat: keep non-ttk widgets in sync with the active theme"
```

---

### Task 5: Wire the theme into the GUI and add the theme menu

Adds the `"theme"` config key and applies the theme at startup. `"theme"` joins `GLOBAL_ONLY_KEYS`: it is a per-machine display preference, and a shortcut profile must not be able to change the user's theme.

This task also adds the regression guard for Risk 1.

**Files:**
- Modify: `microdrop_setup.py:43-59` (`DEFAULT_CONFIG`), `:146` (`GLOBAL_ONLY_KEYS`), `:1460-1472` (`run_gui`), `:977-985` (Options menu)
- Create: `tests/test_headless.py`

**Interfaces:**
- Consumes: `microdrop_theme.apply`, `microdrop_theme.MODES`.
- Produces: `cfg["theme"]`; `LauncherWindow._apply_theme()` which re-applies and saves the chosen mode.

- [ ] **Step 1: Write the failing test**

Create `tests/test_headless.py`:

```python
"""The --launch path must keep working on machines without Tk.

Desktop shortcuts run `microdrop_setup.py --launch`, and microdrop_setup.py
documents at the top of its GUI section that tkinter imports stay
function-local for exactly this reason. microdrop_theme imports tkinter at
module scope, so importing it from microdrop_setup's module scope would break
every shortcut on a headless box — while passing every test on a developer
machine that has Tk. Hence this test.
"""
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Import microdrop_setup with tkinter (and our theme module) poisoned, then
# exercise the headless entry points.
PROBE = """
import sys

class _Blocked:
    def find_module(self, name, path=None):
        if name.split(".")[0] in ("tkinter", "microdrop_theme"):
            raise ImportError("tkinter is unavailable on this machine")
        return None

sys.meta_path.insert(0, _Blocked())
import microdrop_setup
assert microdrop_setup.build_run_args({
    "mode": "dual", "device": "mock", "plugins": [], "contexts": [],
}) is not None
print("ok")
"""


class TestHeadlessImport(unittest.TestCase):
    def test_microdrop_setup_imports_without_tkinter(self):
        result = subprocess.run(
            [sys.executable, "-c", PROBE],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=60)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("ok", result.stdout)

    def test_launch_help_works_without_tkinter(self):
        result = subprocess.run(
            [sys.executable, "microdrop_setup.py", "--help"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=60)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("--launch", result.stdout)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to establish the baseline**

Run: `python -m unittest tests.test_headless -v`
Expected: PASS. This currently passes and must *keep* passing — it is the guard, not a red test. If it fails now, stop: something already imports tkinter at module scope.

- [ ] **Step 3: Add the config key**

In `microdrop_setup.py`, add to `DEFAULT_CONFIG` (after the `"advanced_mode": False,` line):

```python
    "theme": "system",   # "system" | "light" | "dark" (display preference)
```

And extend `GLOBAL_ONLY_KEYS` at line 146:

```python
GLOBAL_ONLY_KEYS = ("install_dir", "preinstall_done", "theme")
```

Update the comment above it to match:

```python
# Machine-global keys never stored in a profile — always inherited from the
# global config so profiles stay portable and survive a missing install.
# "theme" is a per-machine display preference: a shortcut's profile must not
# be able to change how the launcher looks on someone else's desktop.
```

- [ ] **Step 4: Apply the theme at startup**

Replace `run_gui` (`microdrop_setup.py:1460-1472`) with:

```python
def run_gui(cfg, profile=None):
    import tkinter as tk
    import microdrop_theme          # module scope would break --launch
    root = tk.Tk()
    microdrop_theme.apply(root, cfg.get("theme"))
    _set_window_icon(root)
    attach_update_notification(root)

    def open_launcher():
        LauncherWindow(root, cfg, profile=profile)

    if _needs_preinstall(cfg):
        PreInstallWizard(root, cfg, on_done=open_launcher)
    else:
        open_launcher()
    root.mainloop()
```

`_set_window_icon` is added in Task 7. Until then, define this stub directly above `run_gui` so the module stays runnable:

```python
def _set_window_icon(root):
    """Window/taskbar icon. Filled in with a real asset in Task 7."""
```

- [ ] **Step 5: Add the theme menu**

In `LauncherWindow.__init__`, replace the Options menu block (`microdrop_setup.py:977-985`) with:

```python
        # Options menu — advanced mode unlocks every gated checkbox
        self.advanced_var = tk.BooleanVar(value=cfg["advanced_mode"])
        menubar = tk.Menu(root)
        options_menu = tk.Menu(menubar, tearoff=0)
        options_menu.add_checkbutton(
            label="Advanced mode (toggle every plugin)",
            variable=self.advanced_var, command=self._apply_gating)
        # Theme is a machine-global preference, saved outside the profile.
        self.theme_var = tk.StringVar(value=cfg.get("theme", "system"))
        theme_menu = tk.Menu(options_menu, tearoff=0)
        for value, label in (("system", "Match system"),
                             ("light", "Light"),
                             ("dark", "Dark")):
            theme_menu.add_radiobutton(
                label=label, value=value, variable=self.theme_var,
                command=self._apply_theme)
        options_menu.add_cascade(label="Theme", menu=theme_menu)
        menubar.add_cascade(label="Options", menu=options_menu)
        root.configure(menu=menubar)
```

Add the handler as a new method on `LauncherWindow`, directly above `_refresh_version_status`:

```python
    def _apply_theme(self):
        """Switch theme live and remember the choice for next launch."""
        import microdrop_theme
        mode = self.theme_var.get()
        microdrop_theme.apply(self.root, mode)
        self.cfg["theme"] = mode
        # Always the global config: "theme" is in GLOBAL_ONLY_KEYS, so
        # writing it to a profile would silently drop it.
        global_cfg = load_config()
        global_cfg["theme"] = mode
        save_config(global_cfg)
```

- [ ] **Step 6: Run the tests**

Run: `python -m unittest discover tests -v`
Expected: PASS, all tests including the headless guard.

- [ ] **Step 7: Verify the theme actually appears**

Run: `python microdrop_setup.py`
Expected: the window uses Sun Valley. Open Options > Theme and switch between Light and Dark — the change applies immediately without restarting. Close, reopen, and confirm the choice persisted.

- [ ] **Step 8: Commit**

```bash
git add microdrop_setup.py tests/test_headless.py
git commit -m "feat: apply the theme at startup and add a theme menu"
```

---

### Task 6: Fix the hardcoded colours and reliefs

Spec items 1, 2, 3, 4 and the `#b00` in the update banner. These are the changes that make dark mode actually look right.

**Files:**
- Modify: `microdrop_setup.py:660` (`LogPane`), `:727` (`ScrollableFrame`), `:762` (`CollapsibleGroup`), `:1010` and `:1016` (muted labels), `:553-554` (update banner)

**Interfaces:**
- Consumes: `microdrop_theme.register_plain_widget`, the `Muted.TLabel` / `Warn.TLabel` / `Card.TFrame` styles from Task 3.
- Produces: no new API.

- [ ] **Step 1: Theme the log pane**

In `LogPane.__init__` (`microdrop_setup.py:656-662`), replace the body with:

```python
    def __init__(self, parent, height=18):
        import tkinter as tk
        import microdrop_theme
        self._tcl_error = tk.TclError
        self.queue = queue.Queue()
        self.text = tk.Text(parent, height=height, width=100, state="disabled",
                            relief="flat", borderwidth=0,
                            font=("Consolas" if IS_WINDOWS else "monospace", 9))
        # tk.Text ignores ttk themes; register it so it follows theme switches
        # instead of staying a white slab on a dark background.
        microdrop_theme.register_plain_widget(self.text, "log")
        self.text.pack(fill="both", expand=True, padx=8, pady=8)
        self._poll()
```

- [ ] **Step 2: Theme the scroll canvas**

In `ScrollableFrame.__init__` (`microdrop_setup.py:722-728`), replace the canvas creation:

```python
    def __init__(self, parent):
        import tkinter as tk
        from tkinter import ttk
        import microdrop_theme
        self._tcl_error = tk.TclError
        self.container = ttk.Frame(parent)
        self.canvas = tk.Canvas(self.container, highlightthickness=0,
                                borderwidth=0)
        # Same reason as the log pane: an unthemed canvas shows through as a
        # white gutter behind the plugin list.
        microdrop_theme.register_plain_widget(self.canvas, "surface")
```

Leave the rest of the method exactly as it is.

- [ ] **Step 3: Flatten the collapsible group border**

In `CollapsibleGroup.__init__` (`microdrop_setup.py:759-763`), replace the frame creation:

```python
    def __init__(self, parent, title, select_all_command=None, collapsed=False):
        import tkinter as tk
        from tkinter import ttk
        self.frame = ttk.Frame(parent, style="Card.TFrame",
                               padding=PAD_SM)
```

And change the title label (currently `microdrop_setup.py:769`) to use the card title style:

```python
        title_label = ttk.Label(header, text=title, cursor="hand2",
                                style="CardTitle.TLabel")
```

Add the padding constant near the other module constants, after `ICON_PNG_RELPATH` (`microdrop_setup.py:41`):

```python
# Mirrors microdrop_theme.PAD. Duplicated rather than imported because these
# are read at class-body and widget-construction time all over this file, and
# microdrop_theme pulls in tkinter — importing it at module scope would break
# the headless --launch path that desktop shortcuts run.
PAD_SM, PAD_MD, PAD_LG = 4, 8, 12
```

Keep the two in sync by hand; they are three integers and the duplication is
forced by the headless constraint above.

- [ ] **Step 4: Replace the hardcoded greys and red**

At `microdrop_setup.py:1009-1010`:

```python
        ttk.Label(profile_bar, textvariable=self.shortcut_status_var,
                  style="Muted.TLabel").pack(side="left", padx=8)
```

At `microdrop_setup.py:1015-1016`:

```python
        ttk.Label(self.frame, textvariable=self.version_var,
                  style="Muted.TLabel").pack(side="top", anchor="w")
```

In `attach_update_notification.show` (`microdrop_setup.py:552-556`):

```python
    def show(tag):
        ttk.Label(
            bar, style="Warn.TLabel",
            text=f"Launcher update available: {tag} "
                 f"(installed: {launcher_version()})").pack(
            side="left", padx=8, pady=4)
```

- [ ] **Step 5: Run the tests**

Run: `python -m unittest discover tests -v`
Expected: PASS.

- [ ] **Step 6: Verify visually in both themes**

Run: `python microdrop_setup.py`

Check in **dark** mode, then switch to light and check again:
- Plugin list scrolls with no white gutter at the edges
- Profile and version lines are readable grey, not near-black on dark
- Collapsible group borders are flat 1px lines, not bevelled grooves
- If a wizard run is available, the log pane is dark with light text

- [ ] **Step 7: Commit**

```bash
git add microdrop_setup.py
git commit -m "fix: replace hardcoded colours and reliefs with theme styles"
```

---

### Task 7: Header band and window icon

Spec item 10, plus the window icon the launcher has never set.

**Files:**
- Create: `assets/microdrop_icon.png`
- Modify: `microdrop_setup.py` — `_set_window_icon` (stubbed in Task 5), `LauncherWindow.__init__:997-1016`
- Modify: `tests/test_assets.py`

**Interfaces:**
- Consumes: `Header.TLabel`, `Muted.TLabel` from Task 3.
- Produces: `_set_window_icon(root)`; `LauncherWindow._build_header(parent) -> ttk.Frame`.

- [ ] **Step 1: Generate the icon asset**

Tk's `PhotoImage` reads PNG and GIF but not ICO, and `ICON_PNG_RELPATH` (`microdrop_setup.py:41`) points inside the *installed* repo, which does not exist during the wizard. So generate a standalone 64x64 PNG once, at development time, and commit it. Pillow is used here only as a build tool.

```bash
cd "C:/Users/Info/PycharmProjects/microdrop-launcher"
python -c "
from PIL import Image
im = Image.open('Microdrop_Icon.ico')
im.size = (64, 64)
im.load()
im.convert('RGBA').save('assets/microdrop_icon.png')
print('wrote assets/microdrop_icon.png')
"
```

- [ ] **Step 2: Write the failing test**

Add to `tests/test_assets.py`, inside `TestVendoredTheme`:

```python
    def test_window_icon_asset_is_present_and_64px(self):
        # Tk PhotoImage reads PNG, not ICO, and the repo's .ico lives inside
        # the *installed* tree which does not exist during the wizard.
        icon = REPO_ROOT / "assets" / "microdrop_icon.png"
        self.assertTrue(icon.is_file())
        header = icon.read_bytes()[:24]
        self.assertEqual(b"\x89PNG", header[:4])
        # IHDR width/height are big-endian uint32 at offsets 16 and 20.
        width = int.from_bytes(header[16:20], "big")
        height = int.from_bytes(header[20:24], "big")
        self.assertEqual((64, 64), (width, height))
```

- [ ] **Step 3: Run the test**

Run: `python -m unittest tests.test_assets -v`
Expected: PASS if Step 1 produced the file. If it fails on the size assertion, the `.ico` did not contain a 64x64 entry — rerun Step 1 with `im.size = (128, 128)` and change the assertion to match.

- [ ] **Step 4: Implement the window icon**

Replace the `_set_window_icon` stub from Task 5 with:

```python
def _set_window_icon(root):
    """Give the window and taskbar entry the Microdrop icon.

    Purely cosmetic: a missing or unreadable asset leaves the default Tk
    feather rather than stopping the launcher.
    """
    import tkinter as tk
    try:
        icon = tk.PhotoImage(file=str(launcher_assets_dir()
                                      / "assets" / "microdrop_icon.png"))
    except tk.TclError:
        return None
    root.iconphoto(True, icon)
    # Tk drops images that nothing references, blanking the icon.
    root._icon_image = icon
    return icon
```

- [ ] **Step 5: Build the header band**

Add a method to `LauncherWindow`, directly above `_refresh_version_status`:

```python
    def _build_header(self, parent):
        """Icon, title, version badge, and the two repo checkout lines."""
        import tkinter as tk
        from tkinter import ttk
        header = ttk.Frame(parent)
        header.pack(side="top", fill="x", pady=(0, PAD_MD))

        icon = getattr(self.root, "_icon_image", None)
        if icon is not None:
            # 64px asset, 32px slot: subsample takes an integer divisor.
            ttk.Label(header, image=icon.subsample(2)).pack(
                side="left", padx=(0, PAD_MD))

        titles = ttk.Frame(header)
        titles.pack(side="left", fill="x", expand=True)
        ttk.Label(titles, text="Microdrop Launcher",
                  style="Header.TLabel").pack(anchor="w")
        ttk.Label(titles, textvariable=self.version_var,
                  style="Muted.TLabel").pack(anchor="w")

        ttk.Label(header, text=launcher_version() or "dev",
                  style="Muted.TLabel").pack(side="right", anchor="ne")
        return header
```

- [ ] **Step 6: Use it in place of the old rows**

In `LauncherWindow.__init__`, the version label currently sits at `microdrop_setup.py:1014-1016`, *below* the profile bar. Reorder so the header comes first. Replace the profile-bar and version-bar block (`:997-1016`) with:

```python
        # Header band — icon, title, version badge, repo checkout status.
        self.version_var = tk.StringVar()
        self._build_header(self.frame)

        # Profile bar — pick a saved config profile; each shortcut gets one.
        profile_bar = ttk.Frame(self.frame)
        profile_bar.pack(side="top", fill="x", pady=(0, PAD_SM))
        ttk.Label(profile_bar, text="Profile:").pack(side="left")
        self.profile_var = tk.StringVar(
            value=self.profile or DEFAULT_PROFILE_LABEL)
        self.profile_combo = ttk.Combobox(
            profile_bar, textvariable=self.profile_var, state="readonly",
            width=24, values=[DEFAULT_PROFILE_LABEL] + list_profiles())
        self.profile_combo.pack(side="left", padx=PAD_SM)
        self.profile_combo.bind("<<ComboboxSelected>>", self._on_profile_selected)
        self.shortcut_status_var = tk.StringVar()
        ttk.Label(profile_bar, textvariable=self.shortcut_status_var,
                  style="Muted.TLabel").pack(side="left", padx=PAD_MD)
```

`self.version_var` must be created before `_build_header` reads it, which the order above ensures.

- [ ] **Step 7: Run the tests and check visually**

Run: `python -m unittest discover tests -v`
Expected: PASS.

Run: `python microdrop_setup.py`
Expected: header shows the icon, "Microdrop Launcher" in bold, the two repo checkout lines in muted grey, and `dev` on the right (a source run has no stamped version). The window and taskbar show the Microdrop icon rather than the Tk feather.

- [ ] **Step 8: Commit**

```bash
git add assets/microdrop_icon.png microdrop_setup.py tests/test_assets.py
git commit -m "feat: add a header band and a window icon"
```

---

### Task 8: Launch tab grouping, button hierarchy, and window size

Spec items 6, 7, 8, 9.

**Files:**
- Modify: `microdrop_setup.py:962` (geometry), `:988-995` (action buttons), `:1031-1049` (mode and device rows), `:549-561` (update banner frame)

**Interfaces:**
- Consumes: `Card.TFrame`, `CardTitle.TLabel`, `Accent.TButton`.
- Produces: no new API.

- [ ] **Step 1: Group mode and device into cards**

Replace the mode and device blocks (`microdrop_setup.py:1031-1049`) with:

```python
        # Mode and device, as titled cards matching the plugin groups below.
        self.mode_var = tk.StringVar(value=cfg["mode"])
        mode_card = ttk.Frame(content, style="Card.TFrame", padding=PAD_MD)
        mode_card.pack(fill="x", pady=(PAD_SM, PAD_SM))
        ttk.Label(mode_card, text="Mode",
                  style="CardTitle.TLabel").pack(anchor="w")
        mode_row = ttk.Frame(mode_card)
        mode_row.pack(fill="x", pady=(PAD_SM, 0))
        for value, label in MODE_LABELS:
            ttk.Radiobutton(mode_row, text=label, value=value,
                            variable=self.mode_var,
                            command=self._apply_gating).pack(
                side="left", padx=(0, PAD_MD))

        self.device_var = tk.StringVar(value=cfg["device"])
        device_card = ttk.Frame(content, style="Card.TFrame", padding=PAD_MD)
        device_card.pack(fill="x", pady=(0, PAD_MD))
        ttk.Label(device_card, text="Device",
                  style="CardTitle.TLabel").pack(anchor="w")
        device_row = ttk.Frame(device_card)
        device_row.pack(fill="x", pady=(PAD_SM, 0))
        for device in ("dropbot", "opendrop", "mock"):
            ttk.Radiobutton(device_row, text=device, value=device,
                            variable=self.device_var,
                            command=self._apply_gating).pack(
                side="left", padx=(0, PAD_MD))
```

- [ ] **Step 2: Give the actions a hierarchy**

Replace the buttons row (`microdrop_setup.py:988-995`):

```python
        # Actions stay pinned at the bottom; the tabs fill everything above.
        # Launch is the primary action and gets Sun Valley's accent styling.
        buttons_row = ttk.Frame(self.frame)
        buttons_row.pack(side="bottom", pady=PAD_MD)
        ttk.Button(buttons_row, text="Launch", style="Accent.TButton",
                   command=self._launch).pack(side="left", padx=PAD_SM)
        ttk.Button(buttons_row, text="Create Desktop Shortcut",
                   command=self._create_shortcut).pack(side="left", padx=PAD_SM)
        ttk.Button(buttons_row, text="Save & Close",
                   command=self._save_close).pack(side="left", padx=PAD_SM)
```

- [ ] **Step 3: Make the update banner read as a card**

In `attach_update_notification` (`microdrop_setup.py:549-561`), change the bar frame and give Download the accent:

```python
    bar = ttk.Frame(root, style="Card.TFrame")
    bar.pack(side="top", fill="x")
```

and

```python
        ttk.Button(bar, text="Download", style="Accent.TButton",
                   command=lambda: webbrowser.open(LAUNCHER_RELEASES_URL)).pack(
            side="left", padx=4)
```

- [ ] **Step 4: Raise the window size**

Sun Valley's controls are taller than the stock theme, so the old geometry clips the plugin list. At `microdrop_setup.py:962-963`:

```python
        root.geometry("980x860")
        root.minsize(760, 560)
```

- [ ] **Step 5: Run the tests**

Run: `python -m unittest discover tests -v`
Expected: PASS.

- [ ] **Step 6: Verify visually**

Run: `python microdrop_setup.py`

In both themes, confirm:
- Mode and Device render as titled cards consistent with the plugin groups
- Launch is visually the accent/primary button; the other two are default
- Nothing clips at the default window size, and nothing overlaps at the minimum size — drag the window down to `minsize` and check the Launch tab still scrolls rather than truncating

- [ ] **Step 7: Commit**

```bash
git add microdrop_setup.py
git commit -m "feat: group launch options into cards and add button hierarchy"
```

---

### Task 9: Verify the frozen build and update the docs

Risk 3 is only reproducible against a real PyInstaller build — a source run resolves assets from the repo, so it proves nothing about `sys._MEIPASS`.

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: everything above.
- Produces: no code.

- [ ] **Step 1: Build the executable**

```bash
cd "C:/Users/Info/PycharmProjects/microdrop-launcher"
python -m PyInstaller microdrop_setup.spec --noconfirm
```

Expected: builds without error, producing `dist/microdrop_setup.exe`.

- [ ] **Step 2: Confirm the assets are inside the bundle**

A onefile build appends a PyInstaller CArchive rather than a zip, so there is
nothing useful to inspect statically — running it *is* the check.

```bash
./dist/microdrop_setup.exe
```

Expected: the window opens **themed**. If it opens in the stock grey Tk look, `apply()` hit its exception path and returned `"native"` — the `datas` entry from Task 1 Step 4 is wrong or the `theme/` subdirectory was flattened. Diagnose by temporarily removing the `try`/`except` in `apply()` and rerunning to surface the Tcl error.

- [ ] **Step 3: Confirm the headless path still works from the frozen build**

```bash
./dist/microdrop_setup.exe --help
```

Expected: prints usage including `--launch`, exits 0. This is Risk 1 checked against the artifact users actually run.

- [ ] **Step 4: Update the README**

`README.md` currently states that `microdrop_setup.py` is "**Python stdlib only** (tkinter GUI)". That is still true of the runtime imports but no longer tells the whole story, since the repo now vendors theme assets. Replace that paragraph with:

```markdown
`microdrop_setup.py` imports **Python stdlib only** (tkinter GUI) — it must run
before pixi or the project env are installed. Its look comes from the
[Sun Valley ttk theme](https://github.com/rdbende/Sun-Valley-ttk-theme) (MIT),
vendored under `assets/sv_ttk/` as Tcl and PNG assets and loaded directly, so
there is still nothing to pip install. The launcher follows your desktop's
light/dark setting; override it under **Options > Theme**.
```

- [ ] **Step 5: Run the full test suite one last time**

Run: `python -m unittest discover tests -v`
Expected: PASS, with no skips on the development machine.

- [ ] **Step 6: Commit**

```bash
git add README.md
git commit -m "docs: describe the vendored theme and the Theme option"
```

---

## Manual acceptance pass

Run once at the end, in **each** of light and dark, switching live via Options > Theme:

- [ ] Wizard renders correctly, including the log pane during a real install
- [ ] All three tabs — Launch, Git settings, Server Settings
- [ ] Collapsible plugin groups, both expanded and collapsed
- [ ] Scrolled plugin list, with no white gutter at any scroll position
- [ ] Update-notification bar (force it by temporarily returning a fake tag from `check_launcher_update`)
- [ ] Profile switching, which rebuilds the launcher frame
- [ ] Theme choice survives closing and reopening the launcher
- [ ] Menubar is unthemed on Windows and macOS — expected, documented in the spec, not a bug

## Notes carried from the spec

- **Menubar colours** (`tk.Menu`) apply on Linux/X11 only. `sv.tcl`'s `config_menus` returns early on `win32` and `aqua`. Do not chase this.
- **Fonts:** Sun Valley requests "Segoe UI Variable", which ships on Windows 11 only. Elsewhere Tk falls back; the named styles pin "Segoe UI" so the fallback is deliberate.
- **DPI awareness was rejected.** Sun Valley's controls are bitmap spritesheets that do not scale, so enabling `SetProcessDpiAwareness` yields crisp text inside soft, undersized widgets. Revisit separately if HiDPI complaints arrive.
