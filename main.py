import json
from app_state_with_tree import AppStateWithTree
from entities import ObjectSpecification, ObjectSpecificationList
from inference_rules import InferenceRules
from question_tree import QuestionTree
    
if __name__ == "__main__":
    object_spec_list_data: list[ObjectSpecification] = []
    with open("data.json") as fp:
        data = json.load(fp)

    with open("question_values.json", encoding="utf-8") as fp:
        modified_question_values: dict[str, float] = json.load(fp)
        question_values = {tuple(k.split("&&")): v for k, v in modified_question_values.items()}
    
    for i, object_spec_data in enumerate(data):
        object_name: str = object_spec_data.get("name", f"Penyakit Tanpa Nama {i}")
        positive_questions: list[str] = object_spec_data.get("positive_questions", [])
        negative_questions: list[str] = object_spec_data.get("negative_questions", [])
        object_spec_list_data.append(ObjectSpecification(
            name=object_name,
            positive_questions=positive_questions,
            negative_questions=negative_questions
        ))

    tree = QuestionTree.load("question_tree.json")
    inference_rules = InferenceRules.load("rules.json", skip_general_specific_rules=True)
    object_spec_list = ObjectSpecificationList(object_spec_list_data)
    object_spec_list.add_general_questions_with_tree(tree)

    app_state = AppStateWithTree.make_initial(
        object_spec_list=object_spec_list,
        initial_tree=tree,
        inference_rules=inference_rules
    )
    app_state.question_values = question_values

    guess: list[tuple[str, float]] | None = None
    question_no = 0
    while guess is None:
        action = app_state.action()
        if action == "guess":
            guess = app_state.guess_with_percentage()
        else:
            question_no += 1
            action_type, action_value = app_state.ask()
            if action_type == "question":
                question = action_value
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
            elif action_type == "group":
                print(f"Pertanyaan {question_no}: {action_value}")
                questions = tree.get_questions_by_group(action_value)
                for i, q in enumerate(questions):
                    print(f"({i + 1}) {q}")
                
                answer = None
                while answer is None:
                    user_answer = input(f"Jawab (1-{len(questions)}): ")
                    user_answer = user_answer.strip()
                    possibly_valid = True
                    try:
                        user_answer = int(user_answer)
                        if user_answer < 1 or user_answer > len(questions):
                            possibly_valid = False
                    except ValueError:
                        possibly_valid = False

                    if possibly_valid:
                        answer = int(user_answer)

                question = questions[answer - 1]
                new_app_state = app_state.step(question=question, answer=True)    
            else:
                raise NotImplementedError
            
            app_state = new_app_state
    
    print("=== Selesai ===")
    print(guess)
