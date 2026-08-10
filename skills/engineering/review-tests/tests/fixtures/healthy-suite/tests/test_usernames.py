import unittest

from usernames import normalize_username


class NormalizeUsernameTests(unittest.TestCase):
    def test_trims_and_case_folds_the_username(self) -> None:
        self.assertEqual(normalize_username("  Straße  "), "strasse")

    def test_rejects_a_whitespace_only_username(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            normalize_username("   ")

    def test_accepts_twelve_normalized_characters(self) -> None:
        self.assertEqual(normalize_username("ABCDEFGHIJKL"), "abcdefghijkl")

    def test_rejects_thirteen_normalized_characters(self) -> None:
        with self.assertRaisesRegex(ValueError, "at most 12"):
            normalize_username("ABCDEFGHIJKLM")

    def test_rejects_non_string_input(self) -> None:
        with self.assertRaisesRegex(TypeError, "must be a string"):
            normalize_username(123)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
