# (C) Copyright 2024-2026 Blue Ocean Technologies, Inc., Toronto, ON
# All rights reserved.
#
# This software is provided without warranty under the terms of the AGPL-3.0
# license included in LICENSE and may be redistributed only under the
# conditions described in the aforementioned license. The license is also
# available online at https://www.gnu.org/licenses/agpl-3.0.txt
#
# Thanks for using Microdrop open source!

"""Launch path: simple versus fine-grained launch, and the config migration.

Display-free pure-logic tests (no Tk needed). Config files are written to a
temporary directory; the real config is never read.
"""

# Standard library imports.
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import microdrop_setup as ms  # noqa: E402

CUSTOMISED_CONFIG = {
    "mode": "frontend",
    "advanced_mode": True,
    "plugins": ["MicrodropPlugin", "TasksPlugin"],
    "contexts": ["redis_server"],
}


class TestLaunchScript(unittest.TestCase):
    def test_simple_launch_uses_the_simple_scripts(self):
        self.assertEqual(
            "launch_microdrop_simple.ps1",
            ms.launch_script_name(False, is_windows=True),
        )
        self.assertEqual(
            "launch_microdrop_simple.sh",
            ms.launch_script_name(False, is_windows=False),
        )

    def test_advanced_launch_keeps_the_existing_scripts(self):
        self.assertEqual(
            "launch_microdrop.ps1", ms.launch_script_name(True, is_windows=True)
        )
        self.assertEqual(
            "launch_microdrop.sh", ms.launch_script_name(True, is_windows=False)
        )


class TestLaunchCommand(unittest.TestCase):
    def test_simple_launch_passes_only_the_device(self):
        cfg = dict(
            ms.DEFAULT_CONFIG,
            device="portable",
            plugins=["MicrodropPlugin"],
            contexts=["redis_server"],
        )

        self.assertEqual(["--device", "portable"], ms.simple_run_args(cfg))

    def test_windows_command_runs_the_script_with_the_install_dir(self):
        command = ms.build_launch_command(
            "launch_microdrop_simple.ps1",
            "C:/md",
            ["--device", "mock"],
            is_windows=True,
        )

        self.assertEqual("powershell", command[0])
        self.assertEqual(
            [
                "-File",
                "launch_microdrop_simple.ps1",
                "-InstallDir",
                "C:/md",
                "--device",
                "mock",
            ],
            command[-6:],
        )

    def test_posix_command_runs_the_script_with_the_install_dir(self):
        command = ms.build_launch_command(
            "launch_microdrop_simple.sh",
            "/opt/md",
            ["--device", "dropbot"],
            is_windows=False,
        )

        self.assertEqual(
            [
                "bash",
                "launch_microdrop_simple.sh",
                "--install-dir",
                "/opt/md",
                "--device",
                "dropbot",
            ],
            command,
        )


class TestAdvancedSettingsMigration(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.config_file = Path(tmp.name) / "setup_config.json"

        patcher = mock.patch.object(ms, "config_path", return_value=self.config_file)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")

    def test_fresh_install_launches_simple(self):
        self.assertFalse(ms.load_config()["advanced_settings"])

    def test_customised_config_without_the_key_launches_simple(self):
        self.write(self.config_file, CUSTOMISED_CONFIG)

        cfg = ms.load_config()

        self.assertFalse(cfg["advanced_settings"])

    def test_migration_keeps_the_fine_grained_fields(self):
        self.write(self.config_file, CUSTOMISED_CONFIG)

        cfg = ms.load_config()

        for key, value in CUSTOMISED_CONFIG.items():
            self.assertEqual(value, cfg[key])

    def test_an_explicit_advanced_choice_is_kept(self):
        self.write(self.config_file, dict(CUSTOMISED_CONFIG, advanced_settings=True))

        self.assertTrue(ms.load_config()["advanced_settings"])

    def test_profile_without_the_key_does_not_inherit_the_global_choice(self):
        self.write(self.config_file, {"advanced_settings": True})
        self.write(ms.profile_path("lab"), CUSTOMISED_CONFIG)

        cfg = ms.load_config("lab")

        self.assertFalse(cfg["advanced_settings"])
        self.assertEqual("frontend", cfg["mode"])

    def test_profile_choice_is_stored_per_profile(self):
        self.write(self.config_file, {})
        self.write(ms.profile_path("lab"), {"advanced_settings": True})

        self.assertTrue(ms.load_config("lab")["advanced_settings"])
        self.assertFalse(ms.load_config()["advanced_settings"])

    def test_missing_profile_falls_back_to_the_global_choice(self):
        self.write(self.config_file, {"advanced_settings": True})

        self.assertTrue(ms.load_config("gone")["advanced_settings"])


if __name__ == "__main__":
    unittest.main()
