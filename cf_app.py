from cf_belief_calculator import CertaintyFactorBasedBeliefCalculator
from cf_guesser import CertaintyFactorBasedGuesser
from cf_interviewer import CertaintyFactorBasedInterviewer, Question
from entities import ObjectSpecification, ObjectSpecificationList, QuestionAnswer
from inference_rules import InferenceRules

class CertaintyFactorBasedApp:
    def __init__(
            self,
            object_spec_list: ObjectSpecificationList,
            inference_rules: InferenceRules | None = None,
            belief_calculator: CertaintyFactorBasedBeliefCalculator | None = None
    ):
        self.object_spec_list = object_spec_list
        self.guesser = CertaintyFactorBasedGuesser(
            object_spec_list=object_spec_list,
            inference_rules=inference_rules,
            belief_calculator=belief_calculator
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

    inference_rules = InferenceRules.load("rules.json")
    app = CertaintyFactorBasedApp(object_spec_list, inference_rules=inference_rules)

    question_no = 0
    while (question := app.get_question()) is not None:
        guesses = app.guesser.get_all_believed_guesses()
        print(f"Tebakan ({len(guesses)}):", sorted(guesses, reverse=True, key=lambda x: x.confidence), end="\n")
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