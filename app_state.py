from dataclasses import dataclass, field
from entities import ObjectSpecification, ObjectSpecificationList, QuestionAnswer
from evidence_state import EvidenceState
from inference_rules import GeneralSpecificRule, InferenceRules

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

def is_possibly_general_question(question: str, general_specific_rules: list[GeneralSpecificRule]):
    for rule in general_specific_rules:
        if question in rule.specific_questions:
            return False 
    return True

@dataclass
class AppState:
    object_spec_list: ObjectSpecificationList
    evidence_state: EvidenceState
    asked_questions: set[str] = field(default_factory=set)
    question_scope: str | None = None
    question_values: dict[str, float] = field(default_factory=dict)

    @staticmethod
    def make_initial(
            object_spec_list: ObjectSpecificationList,
            inference_rules: InferenceRules
    ):
        return AppState(
            object_spec_list=object_spec_list,
            evidence_state=EvidenceState(
                qa_evidence_map={},
                inference_rules=inference_rules
            ),
        )
    
    def step(self, question: str, answer: bool | None):
        new_asked_questions = self.asked_questions | {question}
        new_question_scope = self.question_scope
        if answer is None:
            new_evidence_state = self.evidence_state
        else:
            new_evidence_state = self.evidence_state.advance(QuestionAnswer(
                question=question,
                answer=answer
            ))
            if self.question_scope is None and answer is True:
                new_question_scope = question

        return AppState(
            object_spec_list=self.object_spec_list,
            evidence_state=new_evidence_state,
            asked_questions=new_asked_questions,
            question_scope=new_question_scope,
            question_values=self.question_values
        )
    
    def action(self):
        if len(self.asked_questions) >= QUESTION_LIMIT:
            return "guess"
        
        possible_guesses = self.get_possible_guesses()
        if len(possible_guesses) <= 1:
            if all(self.is_at_least_one_question_asked(g) for g in possible_guesses):
                return "guess"
        
        valid_questions = self.get_valid_questions()
        if len(valid_questions) == 0:
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
        valid_questions = self.get_valid_questions()
        if len(valid_questions) == 0:
            raise NotImplementedError("No valid questions? Don't ask, then!")
        
        return max(valid_questions, key=lambda x: self.question_values.get(x, 0.0))
    
    def get_valid_questions(self):
        # Find relevant questions
        relevant_questions = self.get_relevant_questions() 
        if len(relevant_questions) == 0:
            return relevant_questions

        if self.question_scope is not None:                    
            # Find specific questions
            specific_questions = self.select_specific_questions(relevant_questions)
            if len(specific_questions) > 0:
                return specific_questions
            
            # Disable the scope since there is no more specific questions
            self.question_scope = None
        
        return self.select_general_questions(relevant_questions)

    def select_specific_questions(self, question_list: list[str]):
        specific_questions: list[str] = []
        general_specific_rules = self.evidence_state.inference_rules.general_specific_rules
        possibly_changed_in_next_iteration = True
        while possibly_changed_in_next_iteration:
            changed = False
            for rule in general_specific_rules:
                extend = False
                if self.question_scope in rule.general_questions:
                    extend = True

                elif (
                        any(sq in rule.general_questions for sq in specific_questions)
                        and all((gq in specific_questions or gq in self.asked_questions) for gq in rule.general_questions)
                    ):
                    extend = True

                if not extend:
                    continue

                for question in rule.specific_questions:
                    if question in question_list and question not in specific_questions:
                        specific_questions.append(question)
                        changed = True

            if not changed:
                possibly_changed_in_next_iteration = False
        
        return specific_questions

    def select_general_questions(self, question_list: list[str]):
        general_questions: list[str] = []
        general_specific_rules = self.evidence_state.inference_rules.general_specific_rules

        for question in question_list:
            if question in general_questions:
                continue

            possibly_general_question = is_possibly_general_question(question, general_specific_rules)
            if possibly_general_question:
                general_questions.append(question)
        
        return general_questions

    def get_relevant_questions(self):
        relevant_questions: list[str] = []
        possible_guesses = self.get_possible_guesses()

        for obj_spec in self.object_spec_list:
            if obj_spec.name not in possible_guesses:
                continue

            for question in obj_spec.positive_questions + obj_spec.negative_questions:
                if question in self.asked_questions:
                    continue
                
                if question in relevant_questions:
                    continue
                
                if question in self.evidence_state.qa_evidence_map:
                    continue

                relevant_questions.append(question)
        
        return relevant_questions