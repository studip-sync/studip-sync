import os
import unittest

import studip_sync
from studip_sync.arg_parser import ARGS
from studip_sync.constants import CONFIG_FILENAME
from studip_sync.course_paths import get_course_save_as


class PathAndConfigFileTest(unittest.TestCase):

    def setUp(self):
        self.original_config_arg = ARGS.config

    def tearDown(self):
        ARGS.config = self.original_config_arg

    def test_get_config_file_from_directory(self):
        ARGS.config = "/tmp/studip-sync-config"
        expected = os.path.join("/tmp/studip-sync-config", CONFIG_FILENAME)
        self.assertEqual(expected, studip_sync.get_config_file())

    def test_get_config_file_from_file_path(self):
        ARGS.config = "/tmp/studip-sync/custom.json"
        self.assertEqual("/tmp/studip-sync/custom.json", studip_sync.get_config_file())

    def test_course_save_path_contains_semester_name_and_id(self):
        course = {
            "semester": "WiSe 2024/25",
            "save_as": "Mathematik / 1",
            "course_id": "abc123"
        }

        path = get_course_save_as(course)
        self.assertEqual("WiSe 2024--25/Mathematik -- 1 [abc123]", path)


if __name__ == "__main__":
    unittest.main()
