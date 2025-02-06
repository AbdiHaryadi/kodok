from dataclasses import dataclass
from typing import Callable
from cf_guesser import CertaintyFactorBasedGuesser, Guess
from entities import ObjectSpecification, QuestionAnswer

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
            object_spec_list: list[ObjectSpecification],
            guesser: CertaintyFactorBasedGuesser
    ):
        self.object_spec_list = object_spec_list
        self._validate_object_specificaton_list()
        self.guesser = guesser
        
        self.all_guesses: list[Guess] = []
        self._latest_all_guesses: bool = False

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

    def get_question(self) -> Question:
        all_guesses = self.guesser.get_all_believed_guesses()
        n_guess = len(all_guesses)
        if n_guess == 0:
            assert len(self.object_spec_list[0].positive_questions) > 0, "All objects are assumed to have a non-empty positive question list."
            question_value = self.object_spec_list[0].positive_questions[0]
        else:
            # TODO: This.
            question_value = all_guesses[0].value
        
        question = Question(value=question_value)
        question.set_callback(lambda a: self.guesser.update(QuestionAnswer(question=question_value, answer=a)))
        return question

class CertaintyFactorBasedApp:
    def __init__(
            self,
            object_spec_list: list[ObjectSpecification]
    ):
        self.object_spec_list = object_spec_list
        self._validate_object_specificaton_list()
        self.guesser = CertaintyFactorBasedGuesser(object_spec_list=object_spec_list)
        self.interviewer = CertaintyFactorBasedInterviewer(
            object_spec_list=object_spec_list,
            guesser=self.guesser
        )

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

    def get_question(self) -> Question | None:
        all_guesses = self.guesser.get_all_believed_guesses()
        if len(all_guesses) == 1:
            return None
        
        return self.interviewer.get_question()
    
    def get_final_result(self) -> str | None:
        all_guesses = self.guesser.get_all_believed_guesses()
        if len(all_guesses) == 1:
            return all_guesses[0].value
        
        return None
    
if __name__ == "__main__":
    object_spec_list = [
        ObjectSpecification(
            name="Demam Berdarah Dengue (DBD)",
            positive_questions=[
                "Demam?",
                "Demam mendadak yang tinggi?",
                "Suhu demam hingga 39 derajat Celcius?",
                "Nyeri kepala?",
                "Menggigil?",
            ]
        ),
        ObjectSpecification(
            name="Tipus",
            positive_questions=[
                "Demam?",
                "Demam berlangsung lebih dari seminggu?",
                "Kelelahan yang berlebihan?",
                "Nyeri kepala?",
            ]
        ),
    ]
    app = CertaintyFactorBasedApp(object_spec_list)
    while (question := app.get_question()) is not None:
        while (answer := input(f"{question.value} (y/n)").lower()) not in ["y", "n"]:
            print("Jawaban tidak valid!")
        
        if answer == "y":
            question.answer(True)
        else:
            question.answer(False)

    print("Hasil:", app.get_final_result())