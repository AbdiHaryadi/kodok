from entities import ObjectSpecification, ObjectSpecificationList, QuestionAnswer


class CertaintyFactorBasedState:
    def __init__(self,
        object_spec_list: ObjectSpecificationList,
        qa_evidence_map: dict[str, bool]
    ):
        self.object_spec_list = object_spec_list
        self.qa_evidence_map = qa_evidence_map

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
        question = qa.question
        if question in self.qa_evidence_map:
            if qa.answer == self.qa_evidence_map[question]:
                return self
            
            raise ValueError(f"Contradiction in question \"{question}\"")
        
        new_qa_evidence_map = {k: v for k, v in self.qa_evidence_map.items()}
        new_qa_evidence_map[question] = qa.answer
        return CertaintyFactorBasedState(
            object_spec_list=self.object_spec_list,
            qa_evidence_map=new_qa_evidence_map
        )
    