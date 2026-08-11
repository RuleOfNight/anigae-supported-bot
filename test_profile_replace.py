import unittest

from profile_replace_utils import normalise_image_url, profile_discord_id


class ProfileReplaceTest(unittest.TestCase):
    def test_extracts_discord_id_from_footer(self):
        self.assertEqual(
            profile_discord_id("Summoner ID: 703335523925753903"),
            703335523925753903,
        )

    def test_rejects_footer_without_summoner_id(self):
        self.assertIsNone(profile_discord_id("Profile"))

    def test_normalises_discord_wrapped_image_url(self):
        self.assertEqual(
            normalise_image_url("<https://example.com/profile.png>"),
            "https://example.com/profile.png",
        )

    def test_rejects_non_http_image_url(self):
        self.assertIsNone(normalise_image_url("file:///profile.png"))


if __name__ == "__main__":
    unittest.main()
