from entities import ObjectSpecification, ObjectSpecificationList, QuestionAnswer
from inference_rules import InferenceRules


class CertaintyFactorBasedState:
    def __init__(self,
        object_spec_list: ObjectSpecificationList,
        qa_evidence_map: dict[str, bool],
        inference_rules: InferenceRules | None = None
    ):
        self.object_spec_list = object_spec_list
        self.qa_evidence_map = qa_evidence_map
        self.inference_rules = inference_rules

    def get_belief(self, obj_spec: ObjectSpecification):
        match_score = 0
        total_questions = 0

        qa_evidence_map = self.qa_evidence_map

        for question in obj_spec.positive_questions:
            total_questions += 1
            if question in qa_evidence_map:
                if qa_evidence_map[question] == True:
                    match_score += 1
                else:
                    match_score -= 1

        for question in obj_spec.negative_questions:
            total_questions += 1
            if question in qa_evidence_map:
                if qa_evidence_map[question] == False:
                    match_score += 1
                else:
                    match_score -= 1

        if total_questions == 0:
            raise ValueError(f"No questions in \"{obj_spec.name}\"")

        belief = max(match_score, 0) / total_questions
        return belief
    
    def advance(self, qa: QuestionAnswer) -> "CertaintyFactorBasedState":
        new_qa_evidence_map = {k: v for k, v in self.qa_evidence_map.items()}
        self._update_qa_evidence_map_with_new_qa(new_qa_evidence_map, qa)

        return CertaintyFactorBasedState(
            object_spec_list=self.object_spec_list,
            qa_evidence_map=new_qa_evidence_map,
            inference_rules=self.inference_rules
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