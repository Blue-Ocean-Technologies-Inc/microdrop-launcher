# (C) Copyright 2024-2026 Blue Ocean Technologies, Inc., Toronto, ON
# All rights reserved.
#
# This software is provided without warranty under the terms of the AGPL-3.0
# license included in LICENSE and may be redistributed only under the
# conditions described in the aforementioned license. The license is also
# available online at https://www.gnu.org/licenses/agpl-3.0.txt
#
# Thanks for using Microdrop open source!

"""Plugin selection: deferred-plugin parsing, the bulk default, stale names.

Display-free pure-logic tests (no Tk needed). plugin_consts.py sources are
written to a temporary directory; the real install is never read.
"""

# Standard library imports.
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import microdrop_setup as ms  # noqa: E402

PLUGIN_CONSTS_SOURCE = textwrap.dedent(
    """
    REQUIRED_PLUGINS = [CorePlugin]
    FRONTEND_PLUGINS = [MicrodropPlugin, TasksPlugin, DeviceViewerPlugin]
    DEFERRED_FRONTEND_PLUGINS = [
        DeferredPlugin(
            spec="image_viewer.plugin:ImageViewerPlugin",
            preload_modules=["image_viewer.dock_pane"],
            dock_panes=[DeferredDockPane(id="viewer", name="Viewer")],
        ),
        DeferredPlugin(spec="user_help_plugin.plugin:UserHelpPlugin"),
        DeferredPlugin(preload_modules=["no_spec"]),
    ]
    DROPBOT_FRONTEND_PLUGINS = [DropbotStatusPlugin]
    BACKEND_PLUGINS = [ElectrodeControllerPlugin]
    DROPBOT_BACKEND_PLUGINS = [DropbotControllerPlugin]
    """
)

ALL_DROPBOT_PLUGINS = [
    "MicrodropPlugin",
    "TasksPlugin",
    "DeviceViewerPlugin",
    "ImageViewerPlugin",
    "UserHelpPlugin",
    "DropbotStatusPlugin",
    "ElectrodeControllerPlugin",
    "DropbotControllerPlugin",
]


def parse_source(source):
    """Parse *source* as a plugin_consts.py file."""
    with tempfile.TemporaryDirectory() as tmp:
        consts_path = Path(tmp) / "plugin_consts.py"
        consts_path.write_text(source, encoding="utf-8")

        return ms.parse_plugin_groups(consts_path)


def make_cfg(plugins, known=(), mode="dual", advanced=False):
    """A config with the plugin selection under test."""
    return dict(
        ms.DEFAULT_CONFIG,
        device="dropbot",
        mode=mode,
        advanced_mode=advanced,
        plugins=list(plugins),
        known_plugins=list(known),
    )


class TestParseDeferredPlugins(unittest.TestCase):
    def test_deferred_specs_parse_to_class_names(self):
        parsed = parse_source(PLUGIN_CONSTS_SOURCE)

        self.assertEqual(
            ["ImageViewerPlugin", "UserHelpPlugin"],
            parsed["DEFERRED_FRONTEND_PLUGINS"],
        )

    def test_checkout_without_deferred_list_parses_empty(self):
        parsed = parse_source("FRONTEND_PLUGINS = [MicrodropPlugin]\n")

        self.assertEqual([], parsed["DEFERRED_FRONTEND_PLUGINS"])
        self.assertEqual(["MicrodropPlugin"], parsed["FRONTEND_PLUGINS"])

    def test_deferred_plugins_join_the_recommended_group(self):
        groups = ms.build_display_groups(parse_source(PLUGIN_CONSTS_SOURCE))
        recommended = next(g for g in groups if g.key == "frontend_recommended")

        self.assertEqual(
            ["DeviceViewerPlugin", "ImageViewerPlugin", "UserHelpPlugin"],
            recommended.plugins,
        )
        self.assertIn("ImageViewerPlugin", ms.offered_plugins(groups))


class TestFullDefaultSet(unittest.TestCase):
    def setUp(self):
        self.groups = ms.build_display_groups(parse_source(PLUGIN_CONSTS_SOURCE))

    def test_everything_ticked_is_the_full_default_set(self):
        self.assertTrue(
            ms.selects_full_default_set(
                self.groups, ALL_DROPBOT_PLUGINS, "dual", "dropbot", False
            )
        )

    def test_a_deselected_plugin_is_not(self):
        selected = [p for p in ALL_DROPBOT_PLUGINS if p != "UserHelpPlugin"]

        self.assertFalse(
            ms.selects_full_default_set(self.groups, selected, "dual", "dropbot", False)
        )

    def test_single_side_and_advanced_launches_never_are(self):
        for mode, advanced in (("frontend", False), ("backend", False)):
            self.assertFalse(
                ms.selects_full_default_set(
                    self.groups, ALL_DROPBOT_PLUGINS, mode, "dropbot", advanced
                )
            )

        self.assertFalse(
            ms.selects_full_default_set(
                self.groups, ALL_DROPBOT_PLUGINS, "dual", "dropbot", True
            )
        )


class TestLaunchPluginNames(unittest.TestCase):
    def setUp(self):
        self.groups = ms.build_display_groups(parse_source(PLUGIN_CONSTS_SOURCE))
        self.messages = []

    def launch_names(self, cfg, groups="checkout"):
        groups = self.groups if groups == "checkout" else groups

        return ms.launch_plugin_names(cfg, groups, self.messages.append)

    def test_stale_full_list_launches_the_full_default_set(self):
        # Saved before ImageViewerPlugin moved to the deferred list and before
        # UserHelpPlugin existed; the latter is new, so it counts as ticked.
        stored = [p for p in ALL_DROPBOT_PLUGINS if p != "UserHelpPlugin"]
        stored.append("RetiredPlugin")
        cfg = make_cfg(stored, known=stored)

        self.assertEqual([], self.launch_names(cfg))

    def test_deselection_passes_the_list_without_stale_names(self):
        stored = ["MicrodropPlugin", "TasksPlugin", "RetiredPlugin"]
        cfg = make_cfg(stored, known=ALL_DROPBOT_PLUGINS + ["RetiredPlugin"])

        self.assertEqual(["MicrodropPlugin", "TasksPlugin"], self.launch_names(cfg))
        self.assertEqual(1, len(self.messages))
        self.assertIn("RetiredPlugin", self.messages[0])

    def test_single_side_mode_passes_its_list(self):
        stored = ["ElectrodeControllerPlugin", "DropbotControllerPlugin"]
        cfg = make_cfg(stored, known=ALL_DROPBOT_PLUGINS, mode="backend")

        self.assertEqual(stored, self.launch_names(cfg))

    def test_empty_selection_stays_the_full_default_set(self):
        self.assertEqual([], self.launch_names(make_cfg([])))

    def test_unreadable_checkout_passes_the_stored_list(self):
        stored = ["MicrodropPlugin", "RetiredPlugin"]

        self.assertEqual(stored, self.launch_names(make_cfg(stored), groups=None))

    def test_run_args_omit_plugins_for_the_full_default_set(self):
        cfg = make_cfg(ALL_DROPBOT_PLUGINS)

        self.assertEqual(["--device", "dropbot"], ms.build_run_args(cfg, []))
        self.assertEqual(
            ["--device", "dropbot", "--plugins", "TasksPlugin"],
            ms.build_run_args(cfg, ["TasksPlugin"]),
        )


if __name__ == "__main__":
    unittest.main()
