import unittest
import os
from cli_presenter.parser import parse_deck, Slide

class TestParser(unittest.TestCase):
    def setUp(self):
        with open("test_deck.md", "w") as f:
            f.write("# Slide 1\n\nContent 1\n---\n# Slide 2\n\nContent 2")
        
        with open("test_deck_empty.md", "w") as f:
            f.write("")

    def tearDown(self):
        if os.path.exists("test_deck.md"):
            os.remove("test_deck.md")
        if os.path.exists("test_deck_empty.md"):
            os.remove("test_deck_empty.md")

    def test_parse_deck(self):
        slides = parse_deck("test_deck.md")
        self.assertEqual(len(slides), 2)
        self.assertIn("# Slide 1", slides[0].content)
        self.assertIn("# Slide 2", slides[1].content)

    def test_parse_empty(self):
        slides = parse_deck("test_deck_empty.md")
        self.assertEqual(len(slides), 1)
        self.assertEqual(slides[0].content, "# No Content")

if __name__ == "__main__":
    unittest.main()
