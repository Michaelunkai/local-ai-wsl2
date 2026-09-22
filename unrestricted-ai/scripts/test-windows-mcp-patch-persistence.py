"""Ensure the windows-mcp launch repair is reapplied and revision-tracked."""

import pathlib
import subprocess
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class WindowsMcpPatchPersistenceTests(unittest.TestCase):
    def test_startup_reapplies_and_tracks_the_launch_patch(self):
        patch_path = ROOT / "scripts" / "patch-windows-mcp.ps1"
        self.assertTrue(patch_path.is_file(), "missing persistent patch script")

        startup = (ROOT / "scripts" / "start-host-tools.ps1").read_text(
            encoding="utf-8"
        )
        self.assertIn('patch-windows-mcp.ps1', startup)

        revision = (ROOT / "integrations" / "integration-revision.mjs").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "uv-tools/windows-mcp/Lib/site-packages/windows_mcp/desktop/service.py",
            revision,
        )

    def test_patch_is_idempotent(self):
        patch_path = ROOT / "scripts" / "patch-windows-mcp.ps1"
        for _ in range(2):
            result = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(patch_path),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)


if __name__ == "__main__":
    unittest.main()
