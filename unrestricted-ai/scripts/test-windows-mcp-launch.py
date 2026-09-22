"""Regression test for the windows-mcp application-launch timeout."""

import unittest
from unittest.mock import patch

from windows_mcp.desktop.service import Desktop


class LaunchWithoutSynchronousDetectionTests(unittest.TestCase):
    def test_successful_launch_returns_without_uia_window_search(self):
        desktop = Desktop()
        expected = (
            "Notepad launch command sent. Inspect the desktop to confirm the "
            "result before the next action."
        )

        with (
            patch.object(desktop, "launch_app", return_value=("", 0, 1234)),
            patch(
                "windows_mcp.desktop.service.uia.WindowControl",
                side_effect=AssertionError(
                    "launch must not perform a synchronous UIA window search"
                ),
            ),
        ):
            self.assertEqual(desktop.app("launch", "notepad"), expected)


if __name__ == "__main__":
    unittest.main()
