import unittest
from unittest.mock import MagicMock

from entities import ObjectSpecification, ObjectSpecificationList
from naive_guesser import NaiveGuess, NaiveGuesser
from naive_interviewer import NaiveInterviewer


class TestNaiveInterviewer(unittest.TestCase):
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

        guesser = NaiveGuesser(object_spec_list=object_spec_list)
        guesser.get_all_possibly_satisfied_guesses = MagicMock(return_value=[
            NaiveGuess(
                value="b",
                satisfied=False
            )
        ])

        interviewer = NaiveInterviewer(
            object_spec_list=object_spec_list,
            guesser=guesser
        )
        question = interviewer.get_question()
        self.assertEqual(question.value, "bp1")
        guesser.get_all_possibly_satisfied_guesses.assert_called()

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

        guesser = NaiveGuesser(object_spec_list=object_spec_list)
        guesser.get_all_possibly_satisfied_guesses = MagicMock(return_value=[])
        guesser.state.qa_evidence_map = {}

        interviewer = NaiveInterviewer(
            object_spec_list=object_spec_list,
            guesser=guesser
        )
        question_1 = interviewer.get_question()
        question_1.answer(False)
        guesser.state.qa_evidence_map[question_1.value] = False

        question_2 = interviewer.get_question()
        self.assertNotEqual(question_1.value, question_2.value)