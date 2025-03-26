import unittest
from unittest.mock import MagicMock

from entities import ObjectSpecification, ObjectSpecificationList, QuestionAnswer
from naive_guesser import NaiveGuesser


class TestNaiveGuesser(unittest.TestCase):
    def test_no_update(self):
        """
        In initial guess, believe all of them can be true
        """

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
        guesser = NaiveGuesser(object_spec_list)

        g = guesser.guess()
        self.assertTrue(any((g.value == x.name for x in object_spec_list)))
        self.assertFalse(g.satisfied)

        all_guesses = guesser.get_all_possibly_satisfied_guesses()
        self.assertEqual(len(all_guesses), 2)
        self.assertEqual(all_guesses[0].value, "Demam Berdarah Dengue (DBD)")
        self.assertFalse(all_guesses[0].satisfied)
        self.assertEqual(all_guesses[1].value, "Tipus")
        self.assertFalse(all_guesses[1].satisfied)

    def test_update(self):
        a_spec = ObjectSpecification(
            name="A",
            positive_questions=["ap1"]
        )
    
        b_spec = ObjectSpecification(
            name="B",
            positive_questions=["bp2"]
        )
    
        object_spec_list = ObjectSpecificationList([
            a_spec,
            b_spec
        ])

        guesser = NaiveGuesser(object_spec_list)
        
        guesser.update(QuestionAnswer(
            question="ap1",
            answer=True
        ))
        g = guesser.guess()
        guess_value = g.value
        self.assertEqual(guess_value, "A", f"Unexpected, got \"{guess_value}\"")

        satisfied = g.satisfied
        self.assertTrue(satisfied)

    def test_repeated_get_all_satisfied_guesses(self):
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

        guesser = NaiveGuesser(object_spec_list)
        guesser.update(QuestionAnswer(
            question="ap1",
            answer=True
        ))
        guesser.reset_all_possibly_satisfied_guesses = MagicMock()

        guesser.get_all_possibly_satisfied_guesses()
        guesser.get_all_possibly_satisfied_guesses()
        guesser.reset_all_possibly_satisfied_guesses.assert_called_once()