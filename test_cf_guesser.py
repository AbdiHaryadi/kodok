import unittest
from unittest.mock import MagicMock

from cf_guesser import CertaintyFactorBasedGuesser
from cf_state import CertaintyFactorBasedState
from entities import ObjectSpecification, ObjectSpecificationList, QuestionAnswer

class TestCertaintyFactorBasedGuesser(unittest.TestCase):
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
        guesser = CertaintyFactorBasedGuesser(object_spec_list)
        guesser.state.get_disbelief = MagicMock(return_value=0.0)
        guesser.state.get_belief = MagicMock(return_value=0.1)

        g = guesser.guess()
        self.assertTrue(any((g.value == x.name for x in object_spec_list)))
        self.assertAlmostEqual(g.confidence, 0.1)

        all_guesses = guesser.get_all_believed_guesses()
        self.assertEqual(len(all_guesses), 2)
        self.assertEqual(all_guesses[0].value, "Demam Berdarah Dengue (DBD)")
        self.assertEqual(all_guesses[0].confidence, 0.1)
        self.assertEqual(all_guesses[1].value, "Tipus")
        self.assertEqual(all_guesses[1].confidence, 0.1)

        guesser.state.get_belief.assert_called()
        guesser.state.get_disbelief.assert_called()

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

        guesser = CertaintyFactorBasedGuesser(object_spec_list)
        guesser.state.get_disbelief = MagicMock(return_value=0.0)
        guesser.state.get_belief = MagicMock(return_value=0.1)
        new_state = CertaintyFactorBasedState(object_spec_list, qa_evidence_map={"ap1": True})
        new_state.get_disbelief = MagicMock(return_value=0.0)

        def side_effect(obj_spec: ObjectSpecification):
            if obj_spec == a_spec:
                return 0.2
            
            return 0.1
        new_state.get_belief = MagicMock(side_effect=side_effect)
        guesser.state.advance = MagicMock(return_value=new_state)

        guesser.update(QuestionAnswer(
            question="ap1",
            answer=True
        ))
        g = guesser.guess()
        guess_value = g.value
        self.assertEqual(guess_value, "A", f"Unexpected, got \"{guess_value}\"")

        confidence = g.confidence
        self.assertEqual(confidence, 0.2)

        guesser.state.get_disbelief.assert_any_call(a_spec)
        guesser.state.get_disbelief.assert_any_call(b_spec)
        guesser.state.get_belief.assert_any_call(a_spec)
        guesser.state.get_belief.assert_any_call(b_spec)
        new_state.get_disbelief.assert_any_call(a_spec)
        new_state.get_disbelief.assert_any_call(b_spec)
        new_state.get_belief.assert_any_call(a_spec)
        new_state.get_belief.assert_any_call(b_spec)

    def test_repeated_get_all_believed_guesses(self):
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

        guesser = CertaintyFactorBasedGuesser(object_spec_list)
        guesser.update(QuestionAnswer(
            question="ap1",
            answer=True
        ))
        guesser.reset_all_believed_guesses = MagicMock()

        guesser.get_all_believed_guesses()
        guesser.get_all_believed_guesses()
        guesser.reset_all_believed_guesses.assert_called_once()

    def test_two_updates(self):
        object_spec_list = ObjectSpecificationList([
            ObjectSpecification(
                name="A",
                positive_questions=["ap1", "x"]
            ),
            ObjectSpecification(
                name="B",
                positive_questions=["bp2"]
            ),
            ObjectSpecification(
                name="C",
                positive_questions=["cp1", "x"]
            )
        ])

        last_state = CertaintyFactorBasedState(object_spec_list, qa_evidence_map={})
        second_last_state = CertaintyFactorBasedState(object_spec_list, qa_evidence_map={})
        second_last_state.advance = MagicMock(return_value=last_state)

        guesser = CertaintyFactorBasedGuesser(object_spec_list)
        first_state = guesser.state
        first_state.advance = MagicMock(return_value=second_last_state)

        first_qa = QuestionAnswer(
            question="x",
            answer=True
        )
        second_qa = QuestionAnswer(
            question="ap1",
            answer=True
        )

        guesser.update(first_qa)
        guesser.update(second_qa)

        self.assertEqual(guesser.state, last_state)
        first_state.advance.assert_called_once_with(first_qa)
        second_last_state.advance.assert_called_once_with(second_qa)
    