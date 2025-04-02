from entities import ObjectSpecificationList, QuestionAnswer
from inference_rules import InferenceRules


class EvidenceState:
    def __init__(self,
        qa_evidence_map: dict[str, bool],
        inference_rules: InferenceRules | None = None,
    ):
        self.qa_evidence_map = qa_evidence_map
        self.inference_rules = inference_rules
    
    def advance(self, qa: QuestionAnswer) -> "EvidenceState":
        new_qa_evidence_map = {k: v for k, v in self.qa_evidence_map.items()}
        self._update_qa_evidence_map_with_new_qa(new_qa_evidence_map, qa)

        return EvidenceState(
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
