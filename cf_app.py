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
    import json

    object_spec_list_data: list[ObjectSpecification] = []
    with open("data.json") as fp:
        data = json.load(fp)

    for i, object_spec_data in enumerate(data):
        object_name: str = object_spec_data.get("name", f"Penyakit Tanpa Nama {i}")
        positive_questions: list[str] = object_spec_data.get("positive_questions", [])
        negative_questions: list[str] = object_spec_data.get("negative_questions", [])
        object_spec_list_data.append(ObjectSpecification(
            name=object_name,
            positive_questions=positive_questions,
            negative_questions=negative_questions
        ))


    object_spec_list = ObjectSpecificationList(object_spec_list_data)
    app = CertaintyFactorBasedApp(object_spec_list)

    question_no = 0
    while (question := app.get_question()) is not None:
        print(app.guesser.get_all_believed_guesses())

        question_no += 1
        while (answer := input(f"Pertanyaan {question_no}: {question.value}\nJawaban (y/t): ").lower()) not in ["y", "t"]:
            print("Jawaban tidak valid!")
        
        if answer == "y":
            question.answer(True)
        else:
            question.answer(False)

    print("Hasil:", app.get_final_result())