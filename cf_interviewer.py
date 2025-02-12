from typing import Callable

from cf_guesser import CertaintyFactorBasedGuesser, Guess
from entities import ObjectSpecificationList

class Question:
    def __init__(self, value: str):
        self.value = value
        self.callbacks: list[Callable[[bool], None]] = []

    def add_callback(self, callback: Callable[[bool], None]):
        self.callbacks.append(callback)

    def answer(self, value: bool):
        for callback in self.callbacks:
            callback(value)

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

        self.asked_questions: set[str] = set()
        self.current_question: Question | None = None
        self._all_questions_asked = False

        self._reset_current_question()

    def _reset_current_question(self):
        all_guesses = self.guesser.get_all_believed_guesses()
        n_guess = len(all_guesses)
        question_value = None
        for object_spec in self.object_spec_list:
            if n_guess > 0 and all(object_spec.name != x.value for x in all_guesses):
                continue

            for potential_question_value in object_spec.positive_questions:
                if potential_question_value not in self.asked_questions:
                    question_value = potential_question_value
                    break

        if question_value is None:
            self.current_question = None
            self._all_questions_asked = True
            return

        question = Question(value=question_value)
        callback = lambda _: self._on_answer(question)
        question.add_callback(callback)
        self.current_question = question

    def has_question(self) -> bool:
        return not self._all_questions_asked

    def get_question(self) -> Question:
        assert self.current_question is not None
        return self.current_question
    
    def _on_answer(self, question: Question):
        if self.current_question is None:
            raise NotImplementedError
        
        if question != self.current_question:
            return  # Ignore
        
        self.asked_questions.add(self.current_question.value)
        self._reset_current_question()