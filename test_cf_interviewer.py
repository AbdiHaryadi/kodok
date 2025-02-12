
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
        guesser.get_all_believed_guesses.assert_called()

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
        guesser.get_all_believed_guesses.assert_called()

    def test_second_question_empty_belief(self):
        object_spec_list = ObjectSpecificationList([
            ObjectSpecification(
                name="b",
                positive_questions=[
                    "bp1",
                    "bp2",
                ]
            )
        ])

        guesser = CertaintyFactorBasedGuesser(object_spec_list=object_spec_list)
        guesser.get_all_believed_guesses = MagicMock(return_value=[])

        interviewer = CertaintyFactorBasedInterviewer(
            object_spec_list=object_spec_list,
            guesser=guesser
        )
        question_1 = interviewer.get_question()
        question_1.answer(False)

        question_2 = interviewer.get_question()
        self.assertNotEqual(question_1.value, question_2.value)

    def test_answered_twice(self):
        object_spec_list = ObjectSpecificationList([
            ObjectSpecification(
                name="b",
                positive_questions=[
                    "bp1",
                    "bp2",
                    "bp3",
                ]
            )
        ])

        guesser = CertaintyFactorBasedGuesser(object_spec_list=object_spec_list)
        guesser.get_all_believed_guesses = MagicMock(return_value=[])

        interviewer = CertaintyFactorBasedInterviewer(
            object_spec_list=object_spec_list,
            guesser=guesser
        )
        question_1 = interviewer.get_question()
        question_1.answer(False)

        first_question_2 = interviewer.get_question()
        question_1.answer(False) # This is wrong.

        second_question_2 = interviewer.get_question()
        self.assertEqual(first_question_2, second_question_2)

    def test_second_question_one_belief(self):
        object_spec_list = ObjectSpecificationList([
            ObjectSpecification(
                name="b",
                positive_questions=[
                    "bp1",
                    "bp2",
                ]
            )
        ])

        guesser = CertaintyFactorBasedGuesser(object_spec_list=object_spec_list)
        guesser.get_all_believed_guesses = MagicMock(return_value=[
            Guess(value="b", confidence=0.1)
        ])

        interviewer = CertaintyFactorBasedInterviewer(
            object_spec_list=object_spec_list,
            guesser=guesser
        )
        question_1 = interviewer.get_question()
        question_1.answer(True)

        question_2 = interviewer.get_question()
        self.assertNotEqual(question_1.value, question_2.value)

    def test_second_question_multiple_belief(self):
        object_spec_list = ObjectSpecificationList([
            ObjectSpecification(
                name="b",
                positive_questions=[
                    "bp1",
                ]
            ),
            ObjectSpecification(
                name="c",
                positive_questions=[
                    "cp1",
                ]
            )
        ])

        guesser = CertaintyFactorBasedGuesser(object_spec_list=object_spec_list)
        guesser.get_all_believed_guesses = MagicMock(return_value=[
            Guess(value="b", confidence=0.1),
            Guess(value="c", confidence=0.1),
        ])

        interviewer = CertaintyFactorBasedInterviewer(
            object_spec_list=object_spec_list,
            guesser=guesser
        )
        question_1 = interviewer.get_question()
        question_1.answer(False)

        question_2 = interviewer.get_question()
        self.assertNotEqual(question_1.value, question_2.value)
        self.assertIn(question_2.value, ["bp1", "cp1"])

    def test_remaining_question_for_no_belief(self):
        object_spec_list = ObjectSpecificationList([
            ObjectSpecification(
                name="b",
                positive_questions=[
                    "bp1",
                ]
            ),
            ObjectSpecification(
                name="c",
                positive_questions=[
                    "cp1",
                ]
            )
        ])

        guesser = CertaintyFactorBasedGuesser(object_spec_list=object_spec_list)
        guesser.get_all_believed_guesses = MagicMock(return_value=[])

        interviewer = CertaintyFactorBasedInterviewer(
            object_spec_list=object_spec_list,
            guesser=guesser
        )
        self.assertTrue(interviewer.has_question())
        
        question_1 = interviewer.get_question()
        self.assertTrue(interviewer.has_question())
        question_1.answer(True)
        self.assertTrue(interviewer.has_question())

        question_2 = interviewer.get_question()
        self.assertTrue(interviewer.has_question())
        question_2.answer(False)
        self.assertFalse(interviewer.has_question())

    def test_smart_question(self):
        object_spec_list = ObjectSpecificationList([
            ObjectSpecification(
                name="a",
                positive_questions=[
                    "ap1",
                    "x"
                ]
            ),
            ObjectSpecification(
                name="b",
                positive_questions=[
                    "bp1",
                ],
                negative_questions=[
                    "x"
                ]
            ),
        ])

        guesser = CertaintyFactorBasedGuesser(object_spec_list=object_spec_list)
        guesser.get_all_believed_guesses = MagicMock(return_value=[])

        interviewer = CertaintyFactorBasedInterviewer(
            object_spec_list=object_spec_list,
            guesser=guesser
        )
        question_1 = interviewer.get_question()
        self.assertEqual(question_1.value, "x")

class TestQuestion(unittest.TestCase):
    def test_add_callback(self):
        q = Question(value="q1")
        callback_1 = MagicMock()
        callback_2 = MagicMock()

        q.add_callback(callback=callback_1)
        q.add_callback(callback=callback_2)
        q.answer(True)

        callback_1.assert_called_once_with(True)
        callback_2.assert_called_once_with(True)
