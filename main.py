from app_state import AppState
from entities import ObjectSpecification, ObjectSpecificationList
from inference_rules import InferenceRules
    
if __name__ == "__main__":
    import json

    object_spec_list_data: list[ObjectSpecification] = []
    with open("data.json") as fp:
        data = json.load(fp)

    inference_rules = InferenceRules.load("rules.json")
    for i, object_spec_data in enumerate(data):
        object_name: str = object_spec_data.get("name", f"Penyakit Tanpa Nama {i}")
        positive_questions: list[str] = object_spec_data.get("positive_questions", [])
        negative_questions: list[str] = object_spec_data.get("negative_questions", [])
        
        possibly_updated_in_next_iteration = True
        while possibly_updated_in_next_iteration:
            possibly_updated_in_next_iteration = False
            for rule in inference_rules.general_specific_rules:
                if any(x in rule.specific_questions for x in positive_questions):
                    for q in rule.general_questions:
                        if q not in positive_questions:
                            positive_questions.append(q)
                            possibly_updated_in_next_iteration = True

        object_spec_list_data.append(ObjectSpecification(
            name=object_name,
            positive_questions=positive_questions,
            negative_questions=negative_questions
        ))
    object_spec_list = ObjectSpecificationList(object_spec_list_data)

    app_state = AppState.make_initial(object_spec_list=object_spec_list, inference_rules=inference_rules)

    guess: list[str] | None = None
    question_no = 0
    while guess is None:
        action = app_state.action()
        if action == "guess":
            guess = app_state.guess()
        else:
            question_no += 1
            question = app_state.ask()
            print(f"Pertanyaan {question_no}: {question}")
            answer = None
            while answer is None:
                user_answer = input("Jawab (ya/tidak/tidak tahu): ")
                user_answer = " ".join(user_answer.strip().split()).lower()
                if user_answer == "ya" or user_answer == "tidak" or user_answer == "tidak tahu":
                    answer = user_answer
                else:
                    print("Jawaban tidak valid!")
            
            if answer == "ya":
                new_app_state = app_state.step(question=question, answer=True)
            elif answer == "tidak":
                new_app_state = app_state.step(question=question, answer=False)
            else:
                new_app_state = app_state.step(question=question, answer=None)
            
            app_state = new_app_state
    
    print("=== Selesai ===")
    print(guess)