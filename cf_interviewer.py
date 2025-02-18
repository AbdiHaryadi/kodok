from typing import Callable

from cf_guesser import CertaintyFactorBasedGuesser, Guess
from entities import ObjectSpecification, ObjectSpecificationList, QuestionAnswer

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

        question_list: list[str] = []
        for object_spec in self.object_spec_list:
            for question in object_spec.positive_questions:
                if question not in question_list:
                    question_list.append(question)

            for question in object_spec.negative_questions:
                if question not in question_list:
                    question_list.append(question)

        self.question_list = question_list

        self._reset_current_question()
        self._need_reset_question = False


    def _reset_current_question(self):
        all_guesses = self.guesser.get_all_believed_guesses()

        best_question_value = None
        best_score = (0.0, 0)
        for question in self.question_list:
            if question not in self.asked_questions:
                cost = self._get_question_cost(question)
                involved = 0
                for object_spec in self.object_spec_list:
                    if not any(object_spec.name == g.value for g in all_guesses):
                        continue

                    if question in object_spec.positive_questions:
                        involved = 1
                    elif question in object_spec.negative_questions:
                        involved = 1
                    # else: ignore

                    if involved == 1:
                        break

                score = (-cost, involved)

                if best_question_value is None or best_score < score:
                    best_question_value = question
                    best_score = score
                # else: ignore

        if best_question_value is None:
            self.current_question = None
            self._all_questions_asked = True
            return

        question = Question(value=best_question_value)
        callback = lambda _: self._on_answer(question)
        question.add_callback(callback)
        self.current_question = question

    def _update_current_question(self):
        if self._need_reset_question:
            self._reset_current_question()
            self._need_reset_question = False

    def _get_question_cost(self, question: str) -> float:
        all_guesses = self.guesser.get_all_believed_guesses()
        n_all_guesses = len(all_guesses)
        if n_all_guesses == 0:
            possible_choice_count = len(self.object_spec_list)
        else:
            possible_choice_count = n_all_guesses
        
        target = possible_choice_count / 2

        # What if the question is answered
        k_true = 0
        k_false = 0
        for object_spec in self.object_spec_list:
            if n_all_guesses > 0 and all(object_spec.name != x.value for x in all_guesses):
                continue

            belief = self._get_belief_after_answering_specific_question(object_spec, question, True)
            if belief > 0.0:
                k_true += 1

            belief = self._get_belief_after_answering_specific_question(object_spec, question, False)
            if belief > 0.0:
                k_false += 1

        cost = abs(target - k_true) + abs(target - k_false)
        return cost 
    
    def _get_belief_after_answering_specific_question(self, obj_spec: ObjectSpecification, specific_question: str, answer: bool):
        new_state = self.guesser.state.advance(QuestionAnswer(
            question=specific_question,
            answer=answer
        ))
        return new_state.get_belief(obj_spec)

    def has_question(self) -> bool:
        self._update_current_question()
        return not self._all_questions_asked

    def get_question(self) -> Question:
        self._update_current_question()
        assert self.current_question is not None
        return self.current_question
    
    def _on_answer(self, question: Question):
        if self.current_question is None:
            raise NotImplementedError
        
        if question != self.current_question:
            return  # Ignore
        
        self.asked_questions.add(self.current_question.value)
        self._need_reset_question = True