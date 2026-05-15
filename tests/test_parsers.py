import unittest

from studip_sync import parsers


class ParsersTest(unittest.TestCase):

    def test_extract_courses_handles_multiple_group_data_blocks(self):
        html = """
        <html>
        <script>
        var MyCoursesData = {
          "groups": [
            {"name": "WiSe 2024/25", "data": [{"ids": ["1", "2"]}]},
            {"name": "SoSe 2024", "data": [{"ids": ["3"]}, {"ids": ["4"]}]}
          ],
          "courses": {
            "1": {"name": "Algebra / I"},
            "2": {"name": "Physik"},
            "3": {"name": "Informatik"},
            "4": {"name": "Mathematik"}
          }
        };
        </script>
        </html>
        """

        courses = list(parsers.extract_courses(html, only_recent_semester=False))
        self.assertEqual(4, len(courses))
        self.assertEqual("Algebra -- I", courses[0]["save_as"])
        self.assertEqual("WiSe 2024--25", courses[0]["semester"])

    def test_extract_courses_recent_only_returns_first_semester(self):
        html = """
        <html>
        <script>
        var MyCoursesData = {
          "groups": [
            {"name": "WiSe 2024/25", "data": [{"ids": ["11"]}]},
            {"name": "SoSe 2024", "data": [{"ids": ["22"]}]}
          ],
          "courses": {
            "11": {"name": "A"},
            "22": {"name": "B"}
          }
        };
        </script>
        </html>
        """

        courses = list(parsers.extract_courses(html, only_recent_semester=True))
        self.assertEqual(1, len(courses))
        self.assertEqual("11", courses[0]["course_id"])
        self.assertEqual("WiSe 2024--25", courses[0]["semester"])

    def test_extract_my_courses_semester_urls(self):
        html = """
        <script>
        var a = "dispatch.php/my_courses/set_semester=old";
        var b = "dispatch.php/my_courses?semester=abc";
        var c = "dispatch.php/my_courses?semester=abc";
        var d = "dispatch.php/my_courses";
        </script>
        """

        urls = parsers.extract_my_courses_semester_urls(html)
        self.assertEqual(
            ["dispatch.php/my_courses/set_semester=old", "dispatch.php/my_courses?semester=abc"],
            urls
        )


if __name__ == "__main__":
    unittest.main()
