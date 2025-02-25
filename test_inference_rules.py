import unittest
from unittest.mock import MagicMock

from inference_rules import AndRule, GeneralSpecificRule, InferenceRules

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

    def test_negative_general_to_specific_chaining(self):
        inference_rules = InferenceRules(
            general_specific_rules=[
                GeneralSpecificRule(
                    general_questions=["a"],
                    specific_questions=["b"]
                ),
                GeneralSpecificRule(
                    general_questions=["b"],
                    specific_questions=["c"]
                )
            ]
        )
        qa_evidence_map = {"a": False}
        inference_rules.update(qa_evidence_map)
        self.assertEqual(qa_evidence_map.get("b", None), False)
        self.assertEqual(qa_evidence_map.get("c", None), False)

    def test_positive_specific_to_general_chaining(self):
        inference_rules = InferenceRules(
            general_specific_rules=[
                GeneralSpecificRule(
                    general_questions=["a"],
                    specific_questions=["b"]
                ),
                GeneralSpecificRule(
                    general_questions=["b"],
                    specific_questions=["c"]
                )
            ]
        )
        qa_evidence_map = {"c": True}
        inference_rules.update(qa_evidence_map)
        self.assertEqual(qa_evidence_map.get("b", None), True)
        self.assertEqual(qa_evidence_map.get("a", None), True)

    def test_using_and_rules(self):
        and_rule = AndRule("a", ["b", "c"])
        and_rule.update = MagicMock(return_value=False)
        inference_rules = InferenceRules(and_rules=[and_rule])
        qa_evidence_map = {"a": False}
        inference_rules.update(qa_evidence_map)
        and_rule.update.assert_called_once_with(qa_evidence_map)
    
class TestAndRule(unittest.TestCase):
    def test_positive_parent(self):
        rule = AndRule(
            parent_question="a",
            child_questions=["b", "c"]
        )

        qa_evidence_map = {"a": True}
        updated = rule.update(qa_evidence_map)
        self.assertTrue(updated)
        self.assertEqual(qa_evidence_map.get("b", None), True)
        self.assertEqual(qa_evidence_map.get("c", None), True)

        updated = rule.update(qa_evidence_map)
        self.assertFalse(updated)
    
    def test_negative_parent_two_childs(self):
        rule = AndRule(
            parent_question="a",
            child_questions=["b", "c"]
        )

        qa_evidence_map = {"a": False}
        updated = rule.update(qa_evidence_map)
        self.assertFalse(updated)
        self.assertIsNone(qa_evidence_map.get("b", None))
        self.assertIsNone(qa_evidence_map.get("c", None))

    def test_negative_parent_two_childs_one_of_them_is_positive(self):
        rule = AndRule(
            parent_question="a",
            child_questions=["b", "c"]
        )

        qa_evidence_map = {"a": False, "b": True}
        updated = rule.update(qa_evidence_map)
        self.assertTrue(updated)
        self.assertEqual(qa_evidence_map.get("c", None), False)

    def test_negative_parent_two_childs_one_of_them_is_negative(self):
        rule = AndRule(
            parent_question="a",
            child_questions=["b", "c"]
        )

        qa_evidence_map = {"a": False, "b": False}
        updated = rule.update(qa_evidence_map)
        self.assertFalse(updated)
        self.assertIsNone(qa_evidence_map.get("c", None))

    def test_negative_parent_three_childs_one_of_them_is_positive(self):
        rule = AndRule(
            parent_question="a",
            child_questions=["b", "c", "d"]
        )

        qa_evidence_map = {"a": False, "b": True}
        updated = rule.update(qa_evidence_map)
        self.assertFalse(updated)
        self.assertIsNone(qa_evidence_map.get("c", None))
        self.assertIsNone(qa_evidence_map.get("d", None))

    def test_negative_parent_three_childs_two_of_them_are_positive(self):
        rule = AndRule(
            parent_question="a",
            child_questions=["b", "c", "d"]
        )

        qa_evidence_map = {"a": False, "b": True, "c": True}
        updated = rule.update(qa_evidence_map)
        self.assertTrue(updated)
        self.assertEqual(qa_evidence_map.get("d", None), False)
    
    def test_two_childs_all_positive(self):
        rule = AndRule(
            parent_question="a",
            child_questions=["b", "c"]
        )

        qa_evidence_map = {"b": True, "c": True}
        updated = rule.update(qa_evidence_map)
        self.assertTrue(updated)
        self.assertEqual(qa_evidence_map.get("a", None), True)

        updated = rule.update(qa_evidence_map)
        self.assertFalse(updated)

    def test_three_childs_two_of_them_positive(self):
        rule = AndRule(
            parent_question="a",
            child_questions=["b", "c", "d"]
        )

        qa_evidence_map = {"b": True, "c": True}
        updated = rule.update(qa_evidence_map)
        self.assertFalse(updated)
        self.assertIsNone(qa_evidence_map.get("a", None))
        self.assertIsNone(qa_evidence_map.get("d", None))

    def test_two_childs_one_negative(self):
        rule = AndRule(
            parent_question="a",
            child_questions=["b", "c"]
        )

        qa_evidence_map = {"b": False}
        updated = rule.update(qa_evidence_map)
        self.assertTrue(updated)
        self.assertEqual(qa_evidence_map.get("a", None), False)