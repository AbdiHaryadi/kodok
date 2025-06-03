from app_state import AppState
from entities import ObjectSpecification, ObjectSpecificationList
from inference_rules import InferenceRules
from typing import Callable, Literal

from question_tree import QuestionTree

import random
random.seed(120)
    
if __name__ == "__main__":
    import json

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

    def run_simulation(answer_function: Callable[[AppState, str], Literal["ya", "tidak", "tidak tahu"]]):
        app_state = AppState.make_initial(
            object_spec_list=object_spec_list,
            initial_tree=tree,
            inference_rules=inference_rules,
        )
        app_state.question_values = question_values

        guess: list[str] | None = None
        question_no = 0
        while guess is None:
            action = app_state.action()
            if action == "guess":
                guess = app_state.guess()
            else:
                print(app_state.get_possible_guesses())
                question_no += 1
                action_type, action_value = app_state.ask()
                print(action_type, action_value)
                answer = answer_function(app_state, action_type, action_value)
                print("Answer:", answer)

                if action_type == "question":
                    question = action_value
                    if answer == "ya":
                        new_app_state = app_state.step(question=question, answer=True)
                    elif answer == "tidak":
                        new_app_state = app_state.step(question=question, answer=False)
                    else:
                        new_app_state = app_state.step(question=question, answer=None)
                elif action_type == "group":
                    questions = tree.get_questions_by_group(action_value)
                    question = questions[answer - 1]
                    new_app_state = app_state.step(question=question, answer=True)
                else:
                    raise NotImplementedError
                
                app_state = new_app_state

        print("Possible guesses:", app_state.get_possible_guesses())
        print("Guess with percentage:", app_state.guess_with_percentage())
        return (guess, question_no)

    for current_object_spec in object_spec_list:
        if current_object_spec.name != "Demam Berdarah Dengue (DBD), Fase Kritis":
            continue
        
        def current_answer_function(state: AppState, action_type: str, action_value: str):
            if action_type == "question":
                question = action_value
                state_if_no = state.step(question, False)
                possible_guesses_if_no = state_if_no.get_possible_guesses()
                if current_object_spec.name not in possible_guesses_if_no:
                    return "ya" # (because we don't want to eliminate it)
                else:
                    return "tidak"
                
            if action_type == "group":
                questions = state.current_tree.get_questions_by_group(action_value)
                possible_answers: list[int] = []
                for i, q in enumerate(questions):
                    state_if_yes = state.step(q, True)
                    possible_guesses_if_yes = state_if_yes.get_possible_guesses()
                    if current_object_spec.name in possible_guesses_if_yes:
                        possible_answers.append(i + 1)
                    # else: ignore
                assert len(possible_answers) > 0
                return random.choice(possible_answers)

            raise NotImplementedError

        print(f"Attempting {current_object_spec.name} ....")
        guess, question_no = run_simulation(current_answer_function)
        print(f"Total question: {question_no}")
        if current_object_spec.name not in guess:
            print(f"Expecting {current_object_spec.name} be included, got {guess}")
            input("(ENTER)")

    def current_answer_function(state: AppState, action_type: str, action_value: str):
        if action_type == "question":
            return "tidak"
        
        if action_type == "group":
            questions = state.current_tree.get_questions_by_group(action_value)
            possible_answers = [i + 1 for i, _ in enumerate(questions)]
            assert len(possible_answers) > 0
            return random.choice(possible_answers)
        
        raise NotImplementedError

    print(f"Attempting no disease ....")
    guess, question_no = run_simulation(current_answer_function)
    print(f"Total question: {question_no}")
    if len(guess) > 0:
        print(f"Expecting no disease, got {guess}")
        input("(ENTER)")
    
