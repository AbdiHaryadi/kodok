from dataclasses import dataclass
from typing import Callable

from cf_guesser import CertaintyFactorBasedGuesser, Guess
from entities import ObjectSpecificationList, QuestionAnswer

@dataclass
class Question:
    value: str
    callback: Callable[[bool], None] | None = None

    def set_callback(self, callback: Callable[[bool], None]):
        self.callback = callback

    def answer(self, value: bool):
        if self.callback is not None:
            self.callback(value)

class CertaintyFactorBasedInterviewer:
    def __init__(
            self,
            object_spec_list: ObjectSpecificationList,
            guesser: CertaintyFactorBasedGuesser
    ):
        self.object_spec_list = object_spec_list
        self.guesser = guesser
        
        self.all_guesses: list[Guess] = []
        self._latest_all_guesses: bool = False

    def get_question(self) -> Question:
        all_guesses = self.guesser.get_all_believed_guesses()
        n_guess = len(all_guesses)
        if n_guess == 0:
            question_value = self.object_spec_list[0].positive_questions[0]
        else:
            question_value = None
            for object_spec in self.object_spec_list:
                if object_spec.name == all_guesses[0].value:
                    question_value = object_spec.positive_questions[0]
        
        return Question(value=question_value)
