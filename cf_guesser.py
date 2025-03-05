from dataclasses import dataclass
from cf_state import CertaintyFactorBasedState
from entities import ObjectSpecification, ObjectSpecificationList, QuestionAnswer
from inference_rules import InferenceRules

@dataclass
class Guess:
    value: str
    confidence: float

class CertaintyFactorBasedGuesser:
    def __init__(
            self,
            object_spec_list: ObjectSpecificationList,
            inference_rules: InferenceRules | None = None
    ):
        self.object_spec_list = object_spec_list
        self._all_believed_guesses: list[Guess] = []
        self.latest_all_believed_guesses: bool = False
        self.state = CertaintyFactorBasedState(
            object_spec_list=object_spec_list,
            qa_evidence_map={},
            inference_rules=inference_rules
        )

    def guess(self) -> Guess:
        all_believed_guesses = self.get_all_believed_guesses()
        if len(all_believed_guesses) == 0:
            return Guess(value=self.object_spec_list[0].name, confidence=0.0)
        
        return max(all_believed_guesses, key=lambda x: x.confidence)

    def _get_belief(self, obj_spec: ObjectSpecification):
        return self.state.get_belief(obj_spec)
    
    def get_all_believed_guesses(self) -> list[Guess]:
        if not self.latest_all_believed_guesses:
            self.reset_all_believed_guesses()
            self.latest_all_believed_guesses = True
    
        return self._all_believed_guesses

    def reset_all_believed_guesses(self):
        result: list[Guess] = []
        for obj_spec in self.object_spec_list:
            disbelief = self.state.get_disbelief(obj_spec)
            if disbelief > 0.0:
                continue

            belief = self._get_belief(obj_spec)
            result.append(Guess(value=obj_spec.name, confidence=belief))
            
        self._all_believed_guesses = result
    
    def update(self, qa: QuestionAnswer):
        self.state = self.state.advance(qa)
        self.reset_all_believed_guesses()
