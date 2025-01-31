from dataclasses import dataclass
from entities import ObjectSpecification, QuestionAnswer

@dataclass
class Guess:
    value: str
    confidence: float

class CertaintyFactorBasedGuesser:
    def __init__(
            self,
            object_spec_list: list[ObjectSpecification]
    ):
        self.object_spec_list = object_spec_list
        self._validate_object_specificaton_list()

        self.qa_evidence_map: dict[str, bool] = {}

    def _validate_object_specificaton_list(self):
        object_spec_list = self.object_spec_list
        n_object_spec = len(object_spec_list)
        if n_object_spec == 0:
            raise ValueError("Object specification list is empty")
        
        object_name_set: set[str] = set()
        for obj_spec in object_spec_list:
            obj_name = obj_spec.name
            if obj_name in object_name_set:
                raise ValueError(f"Duplicate object specification with name \"{obj_name}\"")
            
            object_name_set.add(obj_name)

    def guess(self):
        best_guess_value = ""
        best_belief = -1.0
        for obj_spec in self.object_spec_list:
            belief = self._get_belief(obj_spec)
            if belief > best_belief:
                best_guess_value = obj_spec.name
                best_belief = belief

        return Guess(
            value=best_guess_value,
            confidence=best_belief
        )

    def _get_belief(self, obj_spec: ObjectSpecification):
        expected_positive_answers = 0
        total_positive_questions = 0
        for question in obj_spec.positive_questions:
            total_positive_questions += 1
            if self._is_positive_answer_confirmed(question):
                expected_positive_answers += 1

        if total_positive_questions == 0:
            raise ValueError(f"No positive questions in \"{obj_spec.name}\"")
            
        belief = expected_positive_answers / total_positive_questions
        return belief
    
    def _is_positive_answer_confirmed(self, question: str):
        if question not in self.qa_evidence_map:
            return False
        
        return self.qa_evidence_map[question] == True
    
    def update(self, qa: QuestionAnswer):
        question = qa.question
        if question in self.qa_evidence_map:
            if qa.answer == self.qa_evidence_map[question]:
                return
            
            raise ValueError(f"Contradiction in question \"{question}\"")
        
        self.qa_evidence_map[question] = qa.answer
