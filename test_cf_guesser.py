import unittest
from unittest.mock import MagicMock

from cf_guesser import CertaintyFactorBasedGuesser
from entities import ObjectSpecification, ObjectSpecificationList, QuestionAnswer

class TestCertaintyFactorBasedGuesser(unittest.TestCase):
    def test_no_update(self):
        object_spec_list = ObjectSpecificationList([
            ObjectSpecification(
                name="Demam Berdarah Dengue (DBD)",
                positive_questions=[
                    "Demam?",
                    "Demam mendadak yang tinggi?",
                    "Suhu demam hingga 39 derajat Celcius?",
                    "Nyeri kepala?",
                    "Menggigil?",
                ]
            ),
            ObjectSpecification(
                name="Tipus",
                positive_questions=[
                    "Demam?",
                    "Demam berlangsung lebih dari seminggu?",
                    "Kelelahan yang berlebihan?",
                    "Nyeri kepala?",
                ]
            ),
        ])
        guesser = CertaintyFactorBasedGuesser(object_spec_list)
        g = guesser.guess()
        self.assertTrue(any((g.value == x.name for x in object_spec_list)))
        self.assertAlmostEqual(g.confidence, 0.0)

        all_guesses = guesser.get_all_believed_guesses()
        self.assertSequenceEqual(all_guesses, [])

    def test_single_positive_update(self):
        object_spec_list = ObjectSpecificationList([
            ObjectSpecification(
                name="A",
                positive_questions=["ap1"]
            ),
            ObjectSpecification(
                name="B",
                positive_questions=["bp2"]
            )
        ])

        guesser = CertaintyFactorBasedGuesser(object_spec_list)
        guesser.update(QuestionAnswer(
            question="ap1",
            answer=True
        ))
        g = guesser.guess()
        guess_value = g.value
        self.assertEqual(guess_value, "A", f"Unexpected, got \"{guess_value}\"")

        confidence = g.confidence
        expected_confidence = 1.0
        self.assertAlmostEqual(confidence, expected_confidence, f"Expecting {expected_confidence}, got {confidence}")

        all_guesses = guesser.get_all_believed_guesses()
        self.assertEqual(len(all_guesses), 1)

    def test_repeated_get_all_believed_guesses(self):
        object_spec_list = ObjectSpecificationList([
            ObjectSpecification(
                name="A",
                positive_questions=["ap1"]
            ),
            ObjectSpecification(
                name="B",
                positive_questions=["bp2"]
            )
        ])

        guesser = CertaintyFactorBasedGuesser(object_spec_list)
        guesser.update(QuestionAnswer(
            question="ap1",
            answer=True
        ))
        guesser._get_all_believed_guesses = MagicMock()

        guesser.get_all_believed_guesses()
        guesser.get_all_believed_guesses()
        guesser._get_all_believed_guesses.assert_called_once()
