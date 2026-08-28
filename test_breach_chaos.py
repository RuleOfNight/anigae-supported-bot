import sys
import unittest

try:
    import Commands
except ModuleNotFoundError:
    import commands as Commands
    sys.modules["Commands"] = Commands

from Commands.breach_chaos import BREACH_CHANNEL_ID, ELEMENT_ROLE_IDS, get_breach_chaos_role_id


class BreachChaosTest(unittest.TestCase):
    def test_matches_every_element_only_in_breach_channel(self):
        for element, role_id in ELEMENT_ROLE_IDS.items():
            text = f"The World-Ender's type is now {element.title()}! The storm surges – adapt fast!"
            self.assertEqual(get_breach_chaos_role_id(BREACH_CHANNEL_ID, "Elemental Chaos", text), role_id)
        self.assertIsNone(get_breach_chaos_role_id(1, "Elemental Chaos", "World-Ender's type is now Ground"))
        self.assertIsNone(get_breach_chaos_role_id(BREACH_CHANNEL_ID, "Other Event", "World-Ender's type is now Ground"))

    def test_matches_component_text_with_markdown_heading(self):
        text = """## <:ClanBreach:1451346157963055134> Elemental Chaos

The World-Ender's type is now **Grass** 🍃! The storm surges - adapt fast!
**Next Rotation:** **<t:1787905861:R> [<t:1787905861:D> <t:1787905861:T>]**"""
        self.assertEqual(get_breach_chaos_role_id(BREACH_CHANNEL_ID, "", text), ELEMENT_ROLE_IDS["grass"])

    def test_matches_plain_announcement_text(self):
        text = "Elemental Chaos\nThe World-Ender's type is now **Dark** 🌙!"
        self.assertEqual(get_breach_chaos_role_id(BREACH_CHANNEL_ID, "", text), ELEMENT_ROLE_IDS["dark"])


if __name__ == "__main__":
    unittest.main()
