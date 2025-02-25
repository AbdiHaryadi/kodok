import unittest
from unittest.mock import MagicMock

from cf_state import CertaintyFactorBasedState
from entities import ObjectSpecification, ObjectSpecificationList, QuestionAnswer
from inference_rules import InferenceRules

class TestCertaintyFactorBasedState(unittest.TestCase):
    def test_advance_with_inference_rules(self):
        inference_rules = InferenceRules()
        inference_rules.update = MagicMock()

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
            inference_rules=inference_rules
        )
        next_state = initial_state.advance(QuestionAnswer("ap2", True))
        self.assertTrue(next_state.qa_evidence_map.get("ap2", True))
        inference_rules.update.assert_called_once()
