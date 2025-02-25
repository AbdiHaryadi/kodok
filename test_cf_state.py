import unittest

from cf_state import CertaintyFactorBasedState
from entities import GeneralSpecificRule, ObjectSpecification, ObjectSpecificationList, QuestionAnswer

class TestCertaintyFactorBasedState(unittest.TestCase):
    def test_advance_for_negative_general_to_negative_specific(self):
        initial_state = CertaintyFactorBasedState(
            object_spec_list=ObjectSpecificationList([
                ObjectSpecification(
                    name="a",
                    positive_questions=[
                        "ap1",
                        "ap2",
                        "ap3",
                        "ap4"
                    ]
                ),
                ObjectSpecification(
                    name="b",
                    positive_questions=[
                        "bp1",
                    ]
                )
            ]),
            qa_evidence_map={},
            general_specific_rules=[
                GeneralSpecificRule(
                    general_questions=["ap1", "ap3"],
                    specific_questions=["ap2"]
                ),
                GeneralSpecificRule(
                    general_questions=["ap3"],
                    specific_questions=["bp1"]
                )
            ]
        )
        next_state = initial_state.advance(QuestionAnswer(question="ap1", answer=False))
        self.assertEqual(next_state.qa_evidence_map.get("ap2", None), False)
        self.assertIsNone(next_state.qa_evidence_map.get("ap3", None))

        next_state = next_state.advance(QuestionAnswer(question="ap3", answer=False))
        self.assertEqual(next_state.qa_evidence_map.get("bp1", None), False)

    def test_advance_for_positive_specific_to_positive_general(self):
        initial_state = CertaintyFactorBasedState(
            object_spec_list=ObjectSpecificationList([
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
            ]),
            qa_evidence_map={},
            general_specific_rules=[
                GeneralSpecificRule(
                    general_questions=["ap1", "apwhatever"],
                    specific_questions=["ap2", "bp1"]
                )
            ]
        )
        next_state = initial_state.advance(QuestionAnswer(question="ap2", answer=True))
        self.assertEqual(next_state.qa_evidence_map.get("ap1", None), True)
        self.assertEqual(next_state.qa_evidence_map.get("apwhatever", None), True)
        self.assertIsNone(next_state.qa_evidence_map.get("bp1", None))
    