
import unittest
from unittest.mock import MagicMock

from cf_guesser import CertaintyFactorBasedGuesser, Guess
from cf_interviewer import CertaintyFactorBasedInterviewer, Question
from entities import ObjectSpecification, ObjectSpecificationList

class TestCertaintyFactorBasedInterviewer(unittest.TestCase):
    def test_empty_belief_case(self):
        object_spec_list = ObjectSpecificationList([
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
        ])

        guesser = CertaintyFactorBasedGuesser(object_spec_list=object_spec_list)
        guesser.get_all_believed_guesses = MagicMock(return_value=[])

        interviewer = CertaintyFactorBasedInterviewer(
            object_spec_list=object_spec_list,
            guesser=guesser
        )
        question = interviewer.get_question()
        self.assertIn(question.value, ["ap1", "ap2", "bp1"])
        guesser.get_all_believed_guesses.assert_called_once()

    def test_one_belief_case(self):
        object_spec_list = ObjectSpecificationList([
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
        ])

        guesser = CertaintyFactorBasedGuesser(object_spec_list=object_spec_list)
        guesser.get_all_believed_guesses = MagicMock(return_value=[
            Guess(
                value="b",
                confidence=0.1
            )
        ])

        interviewer = CertaintyFactorBasedInterviewer(
            object_spec_list=object_spec_list,
            guesser=guesser
        )
        question = interviewer.get_question()
        self.assertEqual(question.value, "bp1")
        guesser.get_all_believed_guesses.assert_called_once()

class TestQuestion(unittest.TestCase):
    def test_callback(self):
        q = Question(value="q1")
        callback = MagicMock()

        q.set_callback(callback=callback)
        q.answer(True)

        callback.assert_called_once_with(True)
