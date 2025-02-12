from cf_guesser import CertaintyFactorBasedGuesser
from cf_interviewer import CertaintyFactorBasedInterviewer, Question
from entities import ObjectSpecification, ObjectSpecificationList, QuestionAnswer

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
        if self._should_make_final_result():
            return None
        
        question = self.interviewer.get_question()
        question.add_callback(lambda a: self.guesser.update(QuestionAnswer(
            question=question.value,
            answer=a
        )))
        return question
    
    def _should_make_final_result(self):
        if not self.interviewer.has_question():
            return True
        
        return False
    
    def get_final_result(self) -> str | None:
        if not self._should_make_final_result():
            return None
        
        guess = self.guesser.guess()
        if guess.confidence > 0.0:
            return guess.value
        
        return None
    
if __name__ == "__main__":
    object_spec_list = ObjectSpecificationList([
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
    ])
    app = CertaintyFactorBasedApp(object_spec_list)
    while (question := app.get_question()) is not None:
        while (answer := input(f"{question.value} (y/t)").lower()) not in ["y", "t"]:
            print("Jawaban tidak valid!")
        
        if answer == "y":
            question.answer(True)
        else:
            question.answer(False)

    print("Hasil:", app.get_final_result())