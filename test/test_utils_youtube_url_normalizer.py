import unittest

import test._bootstrap  # noqa: F401

from utils.youtube_url_normalizer import extract_video_id


class YouTubeUrlNormalizerTests(unittest.TestCase):
    def test_extract_from_watch_url(self) -> None:
        self.assertEqual(
            extract_video_id("https://www.youtube.com/watch?v=YCLJz0TANaA&list=abc"),
            "YCLJz0TANaA",
        )

    def test_extract_from_short_url(self) -> None:
        self.assertEqual(extract_video_id("https://youtu.be/dQw4w9WgXcQ"), "dQw4w9WgXcQ")

    def test_extract_from_shorts(self) -> None:
        self.assertEqual(
            extract_video_id("https://www.youtube.com/shorts/abcdEFGhij0"),
            "abcdEFGhij0",
        )

    def test_extract_from_plain_id(self) -> None:
        self.assertEqual(extract_video_id("kfcyvxxK_54"), "kfcyvxxK_54")

    def test_invalid_input_raises(self) -> None:
        with self.assertRaises(ValueError):
            extract_video_id("")


if __name__ == "__main__":
    unittest.main()
