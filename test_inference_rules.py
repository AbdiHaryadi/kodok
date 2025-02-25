import unittest

from inference_rules import GeneralSpecificRule, InferenceRules

class TestInferenceRules(unittest.TestCase):
    def test_update_for_negative_general_to_negative_specific(self):
        inference_rules = InferenceRules(
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
        qa_evidence_map = {"ap1": False}
        inference_rules.update(qa_evidence_map)
        self.assertEqual(qa_evidence_map.get("ap2", None), False)
        self.assertIsNone(qa_evidence_map.get("ap3", None))
        self.assertIsNone(qa_evidence_map.get("bp1", None))

    def test_advance_for_positive_specific_to_positive_general(self):
        inference_rules=InferenceRules(
            general_specific_rules=[
                GeneralSpecificRule(
                    general_questions=["ap1", "apwhatever"],
                    specific_questions=["ap2", "bp1"]
                )
            ]
        )
        qa_evidence_map = {"ap2": True}
        inference_rules.update(qa_evidence_map)
        self.assertEqual(qa_evidence_map.get("ap1", None), True)
        self.assertEqual(qa_evidence_map.get("apwhatever", None), True)
        self.assertIsNone(qa_evidence_map.get("bp1", None))

    # TODO: Test chaining general-specific
    