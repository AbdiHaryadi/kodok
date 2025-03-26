from dataclasses import dataclass
from entities import ObjectSpecification, ObjectSpecificationList, QuestionAnswer
from evidence_state import EvidenceState
from inference_rules import InferenceRules

@dataclass
class NaiveGuess:
    value: str
    satisfied: bool

def is_possibly_satisfied(state: EvidenceState, obj_spec: ObjectSpecification):
    for question in obj_spec.positive_questions:
        if question not in state.qa_evidence_map:
            continue

        if state.qa_evidence_map[question] == False:
            return False
        
    for question in obj_spec.negative_questions:
        if question not in state.qa_evidence_map:
            continue

        if state.qa_evidence_map[question] == True:
            return False
        
    return True

def is_satisfied(state: EvidenceState, obj_spec: ObjectSpecification):
    for question in obj_spec.positive_questions:
        if question not in state.qa_evidence_map:
            return False

        if state.qa_evidence_map[question] == False:
            return False
        
    for question in obj_spec.negative_questions:
        if question not in state.qa_evidence_map:
            return False

        if state.qa_evidence_map[question] == True:
            return False
        
    return True



class NaiveGuesser:
    def __init__(
            self,
            object_spec_list: ObjectSpecificationList,
            inference_rules: InferenceRules | None = None
    ):
        self.object_spec_list = object_spec_list
        self._all_possibly_satisfied_guesses: list[NaiveGuess] = []
        self.latest_all_possibly_satisfied_guesses: bool = False
        self.state = EvidenceState(
            object_spec_list=object_spec_list,
            qa_evidence_map={},
            inference_rules=inference_rules
        )

    def guess(self) -> NaiveGuess:
        all_believed_guesses = self.get_all_possibly_satisfied_guesses()
        return all_believed_guesses[0]
    
    def get_all_possibly_satisfied_guesses(self) -> list[NaiveGuess]:
        if not self.latest_all_possibly_satisfied_guesses:
            self.reset_all_possibly_satisfied_guesses()
            self.latest_all_possibly_satisfied_guesses = True
    
        return self._all_possibly_satisfied_guesses
    
    def reset_all_possibly_satisfied_guesses(self):
        result: list[NaiveGuess] = []
        for obj_spec in self.object_spec_list:
            possibly_satisfied = self.is_possibly_satisfied(obj_spec)
            if not possibly_satisfied:
                continue

            satisfied = self.is_satisfied(obj_spec)
            result.append(NaiveGuess(value=obj_spec.name, satisfied=satisfied))
            
        self._all_possibly_satisfied_guesses = result

    def is_possibly_satisfied(self, obj_spec: ObjectSpecification):
        return is_possibly_satisfied(self.state, obj_spec)

    def is_satisfied(self, obj_spec: ObjectSpecification):
        return is_satisfied(self.state, obj_spec)
    
    def update(self, qa: QuestionAnswer):
        self.state = self.state.advance(qa)
        self.reset_all_possibly_satisfied_guesses()
