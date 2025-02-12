import unittest
from unittest.mock import MagicMock

from cf_app import CertaintyFactorBasedApp
from cf_guesser import Guess
from cf_interviewer import Question
from entities import ObjectSpecification, ObjectSpecificationList, QuestionAnswer

OSL_SAMPLE = ObjectSpecificationList([
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

class TestCertaintyFactorBasedApp(unittest.TestCase):
    def test_empty_belief_case(self):
        object_spec_list = OSL_SAMPLE
        app = CertaintyFactorBasedApp(object_spec_list)
        app.guesser.get_all_believed_guesses = MagicMock(return_value=[])

        app.interviewer.get_question = MagicMock(return_value=Question(
            value="(terserah)"
        ))
        app.interviewer.has_question = MagicMock(return_value=True)
        app.guesser.update = MagicMock()

        result = app.get_final_result()
        self.assertIsNone(result)

        question = app.get_question()
        self.assertEqual(question.value, "(terserah)")

        app.guesser.get_all_believed_guesses.assert_called()
        app.interviewer.get_question.assert_called_once()

        question.answer(True)
        app.guesser.update.assert_called_once_with(QuestionAnswer(
            question="(terserah)",
            answer=True
        ))
        app.interviewer.has_question.assert_called()

    def test_one_belief_case(self):
        object_spec_list = OSL_SAMPLE
        app = CertaintyFactorBasedApp(object_spec_list)
        app.guesser.get_all_believed_guesses = MagicMock(return_value=[
            Guess(
                value="(bebas)",
                confidence=0.1
            )
        ])
        app.guesser.update = MagicMock()

        interviewer_question = Question(
            value="(terserah)"
        )
        app.interviewer.get_question = MagicMock(return_value=interviewer_question)
        app.interviewer.has_question = MagicMock(return_value=True)

        result = app.get_final_result()
        self.assertEqual(result, "(bebas)")

        question = app.get_question()
        self.assertIsNone(question)

        app.guesser.get_all_believed_guesses.assert_called()
        app.interviewer.get_question.assert_not_called()

        app.guesser.update.assert_not_called()
        app.interviewer.has_question.assert_not_called()

    def test_multiple_belief_case(self):
        object_spec_list = OSL_SAMPLE
        app = CertaintyFactorBasedApp(object_spec_list)
        app.guesser.get_all_believed_guesses = MagicMock(return_value=[
            Guess(
                value="(bebas 1)",
                confidence=0.1
            ),
            Guess(
                value="(bebas 2)",
                confidence=0.1
            )
        ])
        app.guesser.update = MagicMock()

        app.interviewer.get_question = MagicMock(return_value=Question(
            value="(terserah)"
        ))
        app.interviewer.has_question = MagicMock(return_value=True)

        result = app.get_final_result()
        self.assertIsNone(result)

        question = app.get_question()
        self.assertEqual(question.value, "(terserah)")

        app.guesser.get_all_believed_guesses.assert_called()
        app.interviewer.get_question.assert_called_once()

        question.answer(False)
        app.guesser.update.assert_called_once_with(QuestionAnswer(
            question="(terserah)",
            answer=False
        ))
        app.interviewer.has_question.assert_called()

    def test_no_remaining_question_and_have_guess(self):
        object_spec_list = OSL_SAMPLE
        app = CertaintyFactorBasedApp(object_spec_list)
        app.guesser.get_all_believed_guesses = MagicMock(return_value=[
            Guess(
                value="(bebas 1)",
                confidence=0.1
            ),
            Guess(
                value="(bebas 2)",
                confidence=0.1
            )
        ])
        app.guesser.update = MagicMock()
        app.guesser.guess = MagicMock(return_value=Guess(
            value="(bebas X)",
            confidence=0.1
        ))

        app.interviewer.get_question = MagicMock(return_value=Question(
            value="(terserah)"
        ))
        app.interviewer.has_question = MagicMock(return_value=False)

        question = app.get_question()
        self.assertIsNone(question)

        app.interviewer.get_question.assert_not_called()

        result = app.get_final_result()
        self.assertEqual(result, "(bebas X)")

    def test_no_remaining_question_but_no_guess(self):
        object_spec_list = OSL_SAMPLE
        app = CertaintyFactorBasedApp(object_spec_list)

        # Distraction
        app.guesser.get_all_believed_guesses = MagicMock(return_value=[
            Guess(
                value="(bebas 1)",
                confidence=0.1
            ),
            Guess(
                value="(bebas 2)",
                confidence=0.1
            )
        ])
        app.guesser.update = MagicMock()
        app.guesser.guess = MagicMock(return_value=Guess(
            value="(bebas X)",
            confidence=0.0
        ))

        app.interviewer.get_question = MagicMock(return_value=Question(
            value="(terserah)"
        ))
        app.interviewer.has_question = MagicMock(return_value=False)

        question = app.get_question()
        self.assertIsNone(question)

        app.interviewer.get_question.assert_not_called()

        result = app.get_final_result()
        self.assertIsNone(result)
