from app_state import AppState
from entities import ObjectSpecification, ObjectSpecificationList
from inference_rules import InferenceRules
from tqdm import tqdm
import random

from question_tree import QuestionTree
random.seed(120)
    
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

    tree = QuestionTree.load("question_tree.json")
    inference_rules = InferenceRules.load("rules.json", skip_general_specific_rules=True)
    
    object_spec_list = ObjectSpecificationList(object_spec_list_data)
    object_spec_list.add_general_questions_with_tree(tree)

    question_values: dict[tuple[str, str], float] = {}
    question_c_map: dict[tuple[str, str], int] = {}

    for epoch in tqdm(range(5000)):
        app_state = AppState.make_initial(
            object_spec_list=object_spec_list,
            initial_tree=tree,
            inference_rules=inference_rules,
        )
        app_state.question_values = question_values

        if random.random() >= 1 / (len(object_spec_list) + 1):
            current_object_spec = object_spec_list[random.randint(0, len(object_spec_list) - 1)]
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
        else:
            def current_answer_function(state: AppState, action_type: str, action_value: str):
                if action_type == "question":
                    return "tidak"
                
                if action_type == "group":
                    questions = state.current_tree.get_questions_by_group(action_value)
                    possible_answers = [i + 1 for i, _ in enumerate(questions)]
                    assert len(possible_answers) > 0
                    return random.choice(possible_answers)
                
                raise NotImplementedError

        guess: list[str] | None = None
        question_no = 0

        prev_states: list[AppState] = []
        prev_actions: list[str] = []
        rewards: list[float] = []

        epsilon = (1 - epoch / 5000) ** 2
        while guess is None:
            action = app_state.action()
            if action == "guess":
                guess = app_state.guess()
            else:
                question_no += 1
                if random.random() > epsilon:
                    action_type, action_value = app_state.ask()  # Exploitation
                else:
                    # Exploration
                    valid_actions = app_state.get_relevant_actions()
                    action_type, action_value = random.choice(valid_actions)

                # RL update
                prev_states.append(app_state)
                prev_actions.append((action_type, action_value))

                answer = current_answer_function(app_state, action_type, action_value)

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

                # RL update
                old_guess_length = len(app_state.get_possible_guesses())
                new_guess_length = len(new_app_state.get_possible_guesses())
                if old_guess_length > 1:
                    reward = -(max(new_guess_length, 1) - 1) / (old_guess_length - 1)
                else:
                    reward = 0.0
                
                rewards.append(reward)
                
                app_state = new_app_state

        current_return = 0 # Start from terminal
        w = 1
        
        t = len(prev_actions) - 1
        while t >= 0:
            current_return = current_return + rewards[t]
            question_c_map[prev_actions[t]] = question_c_map.get(prev_actions[t], 0.0) + w
            question_values[prev_actions[t]] = (
                question_values.get(prev_actions[t], 0.0)
                + (w / question_c_map[prev_actions[t]]) * (current_return - question_values.get(prev_actions[t], 0.0))
            )

            new_prev_action = prev_states[t].ask()
            if new_prev_action != prev_actions[t]:
                break

            b_prob = (1 - epsilon) + epsilon * (1 / len(prev_states[t].get_relevant_actions()))

            w = w * 1 / b_prob
            t -= 1

    print("Final:")
    question_value_tuples = [(k, v) for k, v in question_values.items()]
    question_value_tuples.sort(key=lambda x: x[1], reverse=True)
    for k, v in question_value_tuples:
        print(v, k, sep="\t")

    modified_question_values = {"&&".join(k): v for k, v in question_values.items()}
    with open("question_values.json", encoding="utf-8", mode="w") as fp:
        json.dump(modified_question_values, fp, indent=2)

    