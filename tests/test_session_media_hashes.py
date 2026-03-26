import unittest

from studip_sync.session import Session


class SessionMediaHashesTest(unittest.TestCase):

    def test_media_hash_candidates_support_old_and_new_filename_formats(self):
        new_style = "lecture-title-abcdef123456.mp4"
        old_style = "abcdef123456-lecture-title.mp4"

        new_candidates = Session._media_hash_candidates_from_filename(new_style)
        old_candidates = Session._media_hash_candidates_from_filename(old_style)

        self.assertIn("abcdef123456", new_candidates)
        self.assertIn("abcdef123456", old_candidates)

    def test_existing_media_hashes_is_precomputed_set(self):
        filenames = [
            "video-a-123abc.mp4",
            "123abc-video-b.mp4",
            "nohash.mp4"
        ]

        hashes = Session._existing_media_hashes(filenames)

        self.assertIn("123abc", hashes)
        self.assertNotIn("nohash.mp4", hashes)


if __name__ == "__main__":
    unittest.main()
