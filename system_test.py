from app_state import AppState
from entities import ObjectSpecification, ObjectSpecificationList
from inference_rules import InferenceRules
from typing import Callable, Literal
    
if __name__ == "__main__":
    import json

    object_spec_list_data: list[ObjectSpecification] = []
    with open("data.json") as fp:
        data = json.load(fp)

    with open("question_values.json", encoding="utf-8") as fp:
        question_values: dict[str, float] = json.load(fp)

    for i, object_spec_data in enumerate(data):
        object_name: str = object_spec_data.get("name", f"Penyakit Tanpa Nama {i}")
        positive_questions: list[str] = object_spec_data.get("positive_questions", [])
        negative_questions: list[str] = object_spec_data.get("negative_questions", [])
        object_spec_list_data.append(ObjectSpecification(
            name=object_name,
            positive_questions=positive_questions,
            negative_questions=negative_questions
        ))

    inference_rules = InferenceRules.load("rules.json")
    
    object_spec_list = ObjectSpecificationList(object_spec_list_data)
    general_specific_rules = inference_rules.general_specific_rules
    object_spec_list.add_general_questions(general_specific_rules)

    questions: list[str] = []
    with open("questions.txt") as fp:
        for line in fp:
            line = line.strip()
            questions.append(line)

    def run_simulation(answer_function: Callable[[AppState, str], Literal["ya", "tidak", "tidak tahu"]]):
        app_state = AppState.make_initial(
            object_spec_list=object_spec_list,
            inference_rules=inference_rules,
            questions=questions
        )
        app_state.question_values = question_values

        guess: list[str] | None = None
        question_no = 0
        while guess is None:
            # possible_guesses = app_state.get_possible_guesses()
            # # print(app_state.evidence_state.qa_evidence_map)
            # # print(possible_guesses)
            # if "Tuberkulosis" not in possible_guesses:
            #     print("Something is wrong?")
            #     input()

            action = app_state.action()
            if action == "guess":
                guess = app_state.guess()
            else:
                # print(app_state.get_possible_guesses())
                question_no += 1
                question = app_state.ask()
                # print(question)
                answer = answer_function(app_state, question)
                # print("Answer:", answer)

                if answer == "ya":
                    new_app_state = app_state.step(question=question, answer=True)
                elif answer == "tidak":
                    new_app_state = app_state.step(question=question, answer=False)
                else:
                    new_app_state = app_state.step(question=question, answer=None)
                
                app_state = new_app_state

        print(app_state.get_possible_guesses())
        return (guess, question_no)

    for current_object_spec in object_spec_list:
        # if current_object_spec.name != "Tuberkulosis":
        #     continue

        def current_answer_function(state: AppState, question: str):
            state_if_no = state.step(question, False)
            possible_guesses_if_no = state_if_no.get_possible_guesses()
            if current_object_spec.name not in possible_guesses_if_no:
                return "ya" # (because we don't want to eliminate it)
            else:
                return "tidak"

        print(f"Attempting {current_object_spec.name} ....")
        guess, question_no = run_simulation(current_answer_function)
        print(f"Total question: {question_no}")
        if current_object_spec.name not in guess:
            print(f"Expecting {current_object_spec.name} be included, got {guess}")
            input("(ENTER)")

    def current_answer_function(state: AppState, question: str):
        return "tidak"

    print(f"Attempting no disease ....")
    guess, question_no = run_simulation(current_answer_function)
    print(f"Total question: {question_no}")
    if len(guess) > 0:
        print(f"Expecting no disease, got {guess}")
        input("(ENTER)")
    
