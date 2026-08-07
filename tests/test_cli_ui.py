import unittest

from studip_sync.cli_ui import truncate_text, build_progress_bar, format_controls_hint, \
    format_summary_line


class CliUiTest(unittest.TestCase):

    def test_truncate_text_limits_length(self):
        value = "x" * 100
        truncated = truncate_text(value, max_chars=60)
        self.assertEqual(60, len(truncated))
        self.assertTrue(truncated.endswith("..."))

    def test_truncate_text_keeps_short_values(self):
        value = "short"
        self.assertEqual(value, truncate_text(value, max_chars=60))

    def test_progress_bar_reaches_full(self):
        bar = build_progress_bar(10, 10, width=10)
        self.assertEqual("[==========]", bar)

    def test_controls_hint_non_interactive(self):
        hint = format_controls_hint(False)
        self.assertIn("unavailable", hint)

    def test_summary_line_contains_status_and_counts(self):
        line = format_summary_line(0, {
            "courses_total": 2,
            "courses_file_synced": 1,
            "courses_file_would_sync": 0,
            "files_downloaded": 5,
            "media_downloaded": 3,
            "errors": 0
        })
        self.assertIn("Result=", line)
        self.assertIn("courses=2", line)


if __name__ == "__main__":
    unittest.main()
