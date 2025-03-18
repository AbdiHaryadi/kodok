from cf_belief_calculator import CertaintyFactorBasedBeliefCalculator
from entities import ObjectSpecification, ObjectSpecificationList, QuestionAnswer
from inference_rules import InferenceRules


class CertaintyFactorBasedState:
    def __init__(self,
        object_spec_list: ObjectSpecificationList,
        qa_evidence_map: dict[str, bool],
        inference_rules: InferenceRules | None = None,
        belief_calculator: CertaintyFactorBasedBeliefCalculator | None = None
    ):
        self.object_spec_list = object_spec_list
        self.qa_evidence_map = qa_evidence_map
        self.inference_rules = inference_rules
        
        if belief_calculator is None:
            self.belief_calculator = CertaintyFactorBasedBeliefCalculator()
        else:
            self.belief_calculator = belief_calculator

    def get_belief(self, obj_spec: ObjectSpecification):
        return self.belief_calculator.get_belief(qa_evidence_map=self.qa_evidence_map, obj_spec=obj_spec)
    
    def advance(self, qa: QuestionAnswer) -> "CertaintyFactorBasedState":
        new_qa_evidence_map = {k: v for k, v in self.qa_evidence_map.items()}
        self._update_qa_evidence_map_with_new_qa(new_qa_evidence_map, qa)

        return CertaintyFactorBasedState(
            object_spec_list=self.object_spec_list,
            qa_evidence_map=new_qa_evidence_map,
            inference_rules=self.inference_rules,
            belief_calculator=self.belief_calculator
        )
    
    def _update_qa_evidence_map_with_new_qa(
            self,
            qa_evidence_map: dict[str, bool],
            qa: QuestionAnswer
    ):
        question = qa.question
        if question in qa_evidence_map:
            if qa.answer == qa_evidence_map[question]:
                return
            
            raise ValueError(f"Contradiction in question \"{question}\"")
        
        qa_evidence_map[question] = qa.answer
        if self.inference_rules is None:
            return
        
        self.inference_rules.update(qa_evidence_map)

    def get_disbelief(self, obj_spec: ObjectSpecification) -> float:
        return self.belief_calculator.get_disbelief(qa_evidence_map=self.qa_evidence_map, obj_spec=obj_spec)