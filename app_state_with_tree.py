from dataclasses import dataclass, field

from entities import ObjectSpecification, ObjectSpecificationList, QuestionAnswer
from evidence_state import EvidenceState

import json

from inference_rules import InferenceRules
from question_tree import QuestionTree

QUESTION_LIMIT = 25

def naive_evaluation(state: EvidenceState, obj_spec: ObjectSpecification):
    possibly_satisfied = True
    asked_count = 0
    not_asked_count = 0
    for question in obj_spec.positive_questions:
        if question not in state.qa_evidence_map:
            not_asked_count += 1
            continue

        if state.qa_evidence_map[question] == False:
            possibly_satisfied = False
            break
        else:
            asked_count += 1

    if not possibly_satisfied:
        return (False, -1, -1)

    for question in obj_spec.negative_questions:
        if question not in state.qa_evidence_map:
            not_asked_count += 1
            continue

        if state.qa_evidence_map[question] == True:
            possibly_satisfied = False
            break
        else:
            asked_count += 1

    if not possibly_satisfied:
        return (False, -1, -1)
    
    return (True, asked_count, not_asked_count)

@dataclass
class AppStateWithTree:
    object_spec_list: ObjectSpecificationList
    current_tree: QuestionTree
    evidence_state: EvidenceState
    asked_questions: set[str] = field(default_factory=set)
    question_values: dict[tuple[str, str], float] = field(default_factory=dict)

    @staticmethod
    def make_initial(
            object_spec_list: ObjectSpecificationList,
            initial_tree: QuestionTree,
            inference_rules: InferenceRules | None = None
    ):
        return AppStateWithTree(
            object_spec_list=object_spec_list,
            current_tree=initial_tree,
            evidence_state=EvidenceState(
                qa_evidence_map={},
                inference_rules=inference_rules
            ),
        )
    
    def step(self, question: str, answer: bool | None) -> "AppStateWithTree":
        new_asked_questions = self.asked_questions | {question}
        if answer is None:
            new_evidence_state = self.evidence_state
            new_tree = self.current_tree
        else:
            new_evidence_state = self.evidence_state.advance(QuestionAnswer(
                question=question,
                answer=answer
            ))
            if answer is True:
                chosen_question_tree = None
                for q, v in self.current_tree.questions.items():
                    if q == question:
                        chosen_question_tree = v
                        break

                if chosen_question_tree is None:
                    for gv in self.current_tree.groups.values():
                        found = False
                        for q, v in gv.items():
                            if q != question:
                                continue

                            chosen_question_tree = v
                            found = True
                            break

                        if found:
                            for q in gv.keys():
                                if q == question:
                                    continue

                                new_evidence_state = new_evidence_state.advance(QuestionAnswer(
                                    question=q,
                                    answer=False
                                ))

                            break

                assert chosen_question_tree is not None
                new_tree = chosen_question_tree
            else:
                new_tree = self.current_tree

        new_app_state = AppStateWithTree(
            object_spec_list=self.object_spec_list,
            current_tree=new_tree,
            evidence_state=new_evidence_state,
            asked_questions=new_asked_questions,
            question_values=self.question_values
        )

        ask_exists = False
        while (not ask_exists) and (new_app_state.current_tree.parent is not None):
            ask_exists = len(new_app_state.get_relevant_actions()) > 0
            if not ask_exists:
                new_app_state = AppStateWithTree(
                    object_spec_list=self.object_spec_list,
                    current_tree=new_app_state.current_tree.parent,
                    evidence_state=new_evidence_state,
                    asked_questions=new_asked_questions,
                    question_values=self.question_values
                )

        return new_app_state
    
    def get_relevant_actions(self):
        relevant_obj_spec: list[ObjectSpecification] = []
        for obj_spec in self.object_spec_list:
            eliminated = False
            for q in obj_spec.positive_questions:
                if q in self.evidence_state.qa_evidence_map:
                    if self.evidence_state.qa_evidence_map[q] is False:
                        eliminated = True
                        break

            if eliminated:
                continue

            relevant_obj_spec.append(obj_spec)

        relevant_questions: list[str] = []
        relevant_groups: list[str] = []

        for q in self.current_tree.questions.keys():
            if q in self.asked_questions:
                continue

            # Is it involved in one of the obj_spec?
            involved = False
            for obj_spec in relevant_obj_spec:
                if self.is_involved(q, obj_spec.positive_questions):
                    involved = True
                    break
                
            if involved:
                relevant_questions.append(q)

        for g, gv in self.current_tree.groups.items():
            group_used = False
            for q in gv.keys():
                if q in self.asked_questions:
                    group_used = True
                    break

            if group_used:
                continue

            # It is involved in one of the obj_spec?
            involved = False
            for q in gv.keys():
                for obj_spec in relevant_obj_spec:
                    if self.is_involved(q, obj_spec.positive_questions):
                        involved = True
                        break

                if involved:
                    break
            
            if involved:
                relevant_groups.append(g)
        
        relevant_actions = [("question", x) for x in relevant_questions]
        relevant_actions.extend([("group", x) for x in relevant_groups])
        return relevant_actions
    
    def is_involved(self, q: str, parent_questions: list[str]):
        # The question is involved if:
        # 1. One of its question.
        # 2. One of the child questions in one of its and/or questions.

        if q in parent_questions:
            return True

        if self.evidence_state.inference_rules is None:
            return False

        for q2 in parent_questions:
            if q2 in self.evidence_state.qa_evidence_map:
                continue

            parent_found = False
            for and_rule in self.evidence_state.inference_rules.and_rules:
                if q2 != and_rule.parent_question:
                    continue

                parent_found = True
                if self.is_involved(q, and_rule.child_questions):
                    return True
                
            if parent_found:
                continue

            for or_rule in self.evidence_state.inference_rules.or_rules:
                if q2 != or_rule.parent_question:
                    continue

                if self.is_involved(q, or_rule.child_questions):
                    return True

        return False
    
    def action(self):
        if len(self.asked_questions) >= QUESTION_LIMIT:
            return "guess"
        
        possible_guesses = self.get_possible_guesses()
        if len(possible_guesses) <= 1:
            if all(self.is_at_least_one_question_asked(g) for g in possible_guesses):
                return "guess"
        
        valid_actions = self.get_relevant_actions()
        if len(valid_actions) == 0:
            return "guess"
        
        return "ask"

    def is_at_least_one_question_asked(self, guess: str):
        state = self.evidence_state
        asked_count = 0
        for obj_spec in self.object_spec_list:
            if obj_spec.name != guess:
                continue

            _, asked_count, _ = naive_evaluation(state, obj_spec)
            return asked_count > 0
        
        return False
    
    def guess(self):
        all_result: list[str] = []

        possibly_changed_in_next_iteration = True
        while possibly_changed_in_next_iteration and len(all_result) < 3:
            result: list[str] = []
            max_score = 0.0
            state = self.evidence_state
            for obj_spec in self.object_spec_list:
                if obj_spec.name in all_result:
                    continue

                possibly_satisfied, asked_count, not_asked_count = naive_evaluation(state, obj_spec)
                if not possibly_satisfied:
                    continue

                score = asked_count / (asked_count + not_asked_count)
                if score > max_score:
                    max_score = score
                    result = [obj_spec.name]
                elif score == max_score:
                    result.append(obj_spec.name)
            
            if len(result) == 0 or max_score == 0.0:
                possibly_changed_in_next_iteration = False
            else:
                all_result.extend(result)
        
        return all_result
    
    def guess_with_percentage(self):
        all_result: list[tuple[str, float]] = []

        possibly_changed_in_next_iteration = True
        while possibly_changed_in_next_iteration and len(all_result) < 3:
            result: list[str] = []
            max_score = 0.0
            state = self.evidence_state
            for obj_spec in self.object_spec_list:
                if any(x[0] == obj_spec.name for x in all_result):
                    continue

                possibly_satisfied, asked_count, not_asked_count = naive_evaluation(state, obj_spec)
                if not possibly_satisfied:
                    continue

                score = asked_count / (asked_count + not_asked_count)
                if score > max_score:
                    max_score = score
                    result = [obj_spec.name]
                elif score == max_score:
                    result.append(obj_spec.name)
            
            if len(result) == 0 or max_score == 0.0:
                possibly_changed_in_next_iteration = False
            else:
                for x in result:
                    all_result.append((x, max_score))
        
        return all_result
    
    def get_possible_guesses(self):
        result: list[str] = []
        state = self.evidence_state
        for obj_spec in self.object_spec_list:
            possibly_satisfied, _, _ = naive_evaluation(state, obj_spec)
            if possibly_satisfied:
                result.append(obj_spec.name)

        return result
    
    def ask(self):
        relevant_actions = self.get_relevant_actions()
        if len(relevant_actions) == 0:
            raise NotImplementedError("No relevant actions? Don't ask, then!")
        
        return max(relevant_actions, key=lambda x: self.question_values.get(x, 0.0))
    
    # def get_valid_actions(self):
    #     valid_questions = [q for q in self.current_tree.questions.keys() if q not in self.asked_questions]
    #     valid_groups: list[str] = []
    #     for g, gv in self.current_tree.groups.items():
    #         found = False
    #         for q in gv.keys():
    #             if q in self.asked_questions:
    #                 found = True
    #                 break
            
    #         if not found:
    #             valid_groups.append(g)
        
    #     valid_actions = [("question", x) for x in valid_questions]
    #     valid_actions.extend([("group", x) for x in valid_groups])
    #     return valid_actions
    
    def ask_or_none(self):
        relevant_actions = self.get_relevant_actions()
        if len(relevant_actions) == 0:
            return None
        
        return max(relevant_actions, key=lambda x: self.question_values.get(x, 0.0))
