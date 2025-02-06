import unittest
from unittest.mock import MagicMock

from cf_app import CertaintyFactorBasedApp, Question
from cf_guesser import Guess
from entities import ObjectSpecification, QuestionAnswer

class TestCertaintyFactorBasedApp(unittest.TestCase):
    def test_no_result_for_the_first_time(self):
        object_spec_list = [
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
        ]
        app = CertaintyFactorBasedApp(object_spec_list)
        result = app.get_final_result()
        self.assertIsNone(result)

        question = app.get_question()
        self.assertIsNotNone(question)

    def test_result_exists(self):
        object_spec_list = [
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
        ]
        app = CertaintyFactorBasedApp(object_spec_list)
        app.guesser.get_all_believed_guesses = MagicMock(return_value=[
            Guess(
                value="Tipus",
                confidence=0.1
            )
        ])

        result = app.get_final_result()
        self.assertEqual(result, "Tipus")

        question = app.get_question()
        self.assertIsNone(question)

        app.guesser.get_all_believed_guesses.assert_called()

    def test_handle_question_with_no_believed_guesses(self):
        object_spec_list = [
            ObjectSpecification(
                name="a",
                positive_questions=[
                    "ap1",
                    "ap2",
                ]
            ),
            ObjectSpecification(
                name="b",
                positive_questions=[
                    "bp1",
                ]
            )
        ]

        app = CertaintyFactorBasedApp(object_spec_list)
        app.guesser.get_all_believed_guesses = MagicMock(return_value=[])
        app.guesser.update = MagicMock()

        question = app.get_question()
        if question is None:
            self.fail()
            return

        self.assertIn(question.value, ["ap1", "ap2", "bp1"])

        question.answer(True)
        app.guesser.update.assert_called_once_with(QuestionAnswer(question=question.value, answer=True))

    def test_handle_question_with_believed_guesses(self):
        object_spec_list = [
            ObjectSpecification(
                name="a",
                positive_questions=[
                    "ap1",
                    "ap2",
                ]
            ),
            ObjectSpecification(
                name="b",
                positive_questions=[
                    "same question",
                    "bp1",
                ]
            ),
            ObjectSpecification(
                name="c",
                positive_questions=[
                    "same question",
                    "cp1",
                ]
            ),
        ]

        app = CertaintyFactorBasedApp(object_spec_list)
        app.guesser.get_all_believed_guesses = MagicMock(return_value=[
            Guess(
                value="b",
                confidence=0.2
            ),
            Guess(
                value="c",
                confidence=0.2
            ),
        ])
        app.guesser.update = MagicMock()

        result = app.get_final_result()
        self.assertIsNone(result)

        question = app.get_question()
        if question is None:
            self.fail()
            return
        
        self.assertIn(question.value, ["b", "c"])

        question.answer(False)
        app.guesser.update.assert_called_once_with(QuestionAnswer(question=question.value, answer=False))

class TestQuestion(unittest.TestCase):
    def test_callback(self):
        q = Question(value="q1")
        callback = MagicMock()

        q.set_callback(callback=callback)
        q.answer(True)

        callback.assert_called_once_with(True)
