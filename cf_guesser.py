from dataclasses import dataclass
from entities import ObjectSpecification, ObjectSpecificationList, QuestionAnswer

@dataclass
class Guess:
    value: str
    confidence: float

class CertaintyFactorBasedGuesser:
    def __init__(
            self,
            object_spec_list: ObjectSpecificationList
    ):
        self.object_spec_list = object_spec_list
        self.qa_evidence_map: dict[str, bool] = {}
        self._all_believed_guesses: list[Guess] = []
        self.latest_all_believed_guesses: bool = False

    def guess(self) -> Guess:
        all_believed_guesses = self.get_all_believed_guesses()
        if len(all_believed_guesses) == 0:
            return Guess(value=self.object_spec_list[0].name, confidence=0.0)
        
        return max(all_believed_guesses, key=lambda x: x.confidence)

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
    
    def get_all_believed_guesses(self) -> list[Guess]:
        if not self.latest_all_believed_guesses:
            self._all_believed_guesses = self._get_all_believed_guesses()
            self.latest_all_believed_guesses = True
    
        return self._all_believed_guesses

    def _get_all_believed_guesses(self):
        result: list[Guess] = []
        for obj_spec in self.object_spec_list:
            belief = self._get_belief(obj_spec)
            if belief > 0.0:
                result.append(Guess(value=obj_spec.name, confidence=belief))
            
        return result
    
    def update(self, qa: QuestionAnswer):
        question = qa.question
        if question in self.qa_evidence_map:
            if qa.answer == self.qa_evidence_map[question]:
                return
            
            raise ValueError(f"Contradiction in question \"{question}\"")
        
        self.qa_evidence_map[question] = qa.answer
