"""Regression tests for coordinate-based Windows desktop actions."""

import unittest
from unittest.mock import patch

import workspace_api


class DesktopCoordinateActionTests(unittest.TestCase):
    def test_type_accepts_snapshot_coordinates(self):
        with patch.object(
            workspace_api, "call_host_tool", return_value={"isError": False}
        ) as call:
            result = workspace_api.interact_windows_desktop(
                action="type",
                loc=[1782, 1138],
                text="marker",
            )

        self.assertEqual(result, {"isError": False})
        call.assert_called_once_with(
            "windows_ui",
            "Type",
            {
                "loc": [1782, 1138],
                "text": "marker",
                "clear": False,
                "press_enter": False,
            },
        )

    def test_click_accepts_snapshot_coordinates(self):
        with patch.object(
            workspace_api, "call_host_tool", return_value={"isError": False}
        ) as call:
            workspace_api.interact_windows_desktop(
                action="click",
                loc=[1828, 380],
            )

        call.assert_called_once_with(
            "windows_ui",
            "Click",
            {
                "loc": [1828, 380],
                "button": "left",
                "clicks": 1,
            },
        )


if __name__ == "__main__":
    unittest.main()
