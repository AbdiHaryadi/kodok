from cf_guesser import CertaintyFactorBasedGuesser
from cf_interviewer import CertaintyFactorBasedInterviewer, Question
from entities import GeneralSpecificRule, ObjectSpecification, ObjectSpecificationList, QuestionAnswer

class CertaintyFactorBasedApp:
    def __init__(
            self,
            object_spec_list: ObjectSpecificationList,
            general_specific_rules: list[GeneralSpecificRule] = []
    ):
        self.object_spec_list = object_spec_list
        self.guesser = CertaintyFactorBasedGuesser(
            object_spec_list=object_spec_list,
            general_specific_rules=general_specific_rules
        )
        self.interviewer = CertaintyFactorBasedInterviewer(
            object_spec_list=object_spec_list,
            guesser=self.guesser
        )

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

    with open("rules.json") as fp:
        data = json.load(fp)
        general_specific_rules = [GeneralSpecificRule.from_dict(x) for x in data["general_specific"]]

    app = CertaintyFactorBasedApp(object_spec_list, general_specific_rules=general_specific_rules)

    question_no = 0
    while (question := app.get_question()) is not None:
        print("Tebakan:", app.guesser.get_all_believed_guesses(), end="\n")
        print("Bukti:", app.guesser.state.qa_evidence_map, end="\n")
        print("---")

        question_no += 1
        while (answer := input(f"Pertanyaan {question_no}: {question.value}\nJawaban (y/t): ").lower()) not in ["y", "t"]:
            print("Jawaban tidak valid!")
        
        if answer == "y":
            question.answer(True)
        else:
            question.answer(False)

    print("Hasil:", app.get_final_result())