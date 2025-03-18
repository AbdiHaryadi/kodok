from entities import ObjectSpecification

class CertaintyFactorBasedBeliefCalculator:
    def get_belief(self, qa_evidence_map: dict[str, bool], obj_spec: ObjectSpecification) -> float:
        unclipped_belief = self._get_unclipped_belief(qa_evidence_map, obj_spec)
        belief = max(unclipped_belief, 0)
        return belief
    
    def _get_unclipped_belief(self, qa_evidence_map: dict[str, bool], obj_spec: ObjectSpecification) -> float:
        match_score = 0
        total_questions = 0

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

        unclipped_belief = match_score / total_questions
        return unclipped_belief
    
    def get_disbelief(self, qa_evidence_map: dict[str, bool], obj_spec: ObjectSpecification) -> float:
        unclipped_belief = self._get_unclipped_belief(qa_evidence_map, obj_spec)
        disbelief = max(-unclipped_belief, 0)
        return disbelief
