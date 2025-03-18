from entities import ObjectSpecification

class CertaintyFactorBasedBeliefCalculator:
    def __init__(self, weights: dict[str, float] = {}):
        self.weights = weights

    def get_belief(self, qa_evidence_map: dict[str, bool], obj_spec: ObjectSpecification) -> float:
        unclipped_belief = self._get_unclipped_belief(qa_evidence_map, obj_spec)
        belief = max(unclipped_belief, 0)
        return belief
    
    def _get_unclipped_belief(self, qa_evidence_map: dict[str, bool], obj_spec: ObjectSpecification) -> float:
        match_score = 0.0
        total_score = 0.0
        question_exists = False

        for question in obj_spec.positive_questions:
            question_exists = True
            weight = self.weights.get(question, 1.0)
            total_score += weight
            if question in qa_evidence_map:
                if qa_evidence_map[question] == True:
                    match_score += weight
                else:
                    match_score -= weight

        for question in obj_spec.negative_questions:
            question_exists = True
            weight = self.weights.get(question, 1.0)
            total_score += weight
            if question in qa_evidence_map:
                if qa_evidence_map[question] == False:
                    match_score += weight
                else:
                    match_score -= weight

        if not question_exists:
            raise ValueError(f"No questions in \"{obj_spec.name}\"")

        unclipped_belief = match_score / total_score
        return unclipped_belief
    
    def get_disbelief(self, qa_evidence_map: dict[str, bool], obj_spec: ObjectSpecification) -> float:
        unclipped_belief = self._get_unclipped_belief(qa_evidence_map, obj_spec)
        disbelief = max(-unclipped_belief, 0)
        return disbelief
