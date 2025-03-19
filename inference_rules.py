from dataclasses import dataclass, field
import json

def update_qa_evidence_map(qa_evidence_map: dict[str, bool], question: str, answer: bool):
    if question in qa_evidence_map:
        if qa_evidence_map[question] == answer:
            return False

        raise ValueError(f"Contradiction detected: For {qa_evidence_map=}, it leads to contradiction in question {question} when answering {answer}.")
    
    qa_evidence_map[question] = answer
    return True

@dataclass
class GeneralSpecificRule:
    general_questions: list[str] = field(default_factory=lambda: [])
    specific_questions: list[str] = field(default_factory=lambda: [])

    @staticmethod
    def from_dict(data: dict[str, list[str]]):
        return GeneralSpecificRule(
            general_questions=data["general_questions"],
            specific_questions=data["specific_questions"],
        )
    
    def update(self, qa_evidence_map: dict[str, bool]):
        updated = self._negative_general_to_specific_update(qa_evidence_map)
        updated = self._positive_specific_to_general_update(qa_evidence_map) or updated
        return updated
    
    def _negative_general_to_specific_update(self, qa_evidence_map: dict[str, bool]):
        updated = False

        negate_specific_questions = False
        for q in self.general_questions:
            if q in qa_evidence_map and (qa_evidence_map[q] == False):
                negate_specific_questions = True
                break

        if negate_specific_questions:
            for q in self.specific_questions:
                qa_evidence_update = update_qa_evidence_map(qa_evidence_map, question=q, answer=False)
                if qa_evidence_update:
                    updated = True
        
        return updated
    
    def _positive_specific_to_general_update(self, qa_evidence_map: dict[str, bool]):
        updated = False

        satisfy_general_questions = False
        for q in self.specific_questions:
            if q in qa_evidence_map and (qa_evidence_map[q] == True):
                satisfy_general_questions = True
                break

        if satisfy_general_questions:
            for q in self.general_questions:
                qa_evidence_update = update_qa_evidence_map(qa_evidence_map, question=q, answer=True)
                if qa_evidence_update:
                    updated = True
        
        return updated
    
@dataclass
class AndRule:
    parent_question: str
    child_questions: list[str]

    @staticmethod
    def from_dict(data: dict[str, list[str]]):
        return AndRule(
            parent_question=data["parent_question"],
            child_questions=data["child_questions"],
        )
    
    def update(self, qa_evidence_map: dict[str, bool]):
        if self.parent_question in qa_evidence_map:
            if qa_evidence_map[self.parent_question] == True:
                return self._update_all_childs_to_positive(qa_evidence_map)
            
            unanswered_questions = []
            found_false_answer = False
            for q in self.child_questions:
                if q not in qa_evidence_map:
                    unanswered_questions.append(q)
                elif qa_evidence_map[q] == False:
                    found_false_answer = True
                    break

            if found_false_answer:
                return False

            if len(unanswered_questions) == 1:
                return update_qa_evidence_map(qa_evidence_map, question=unanswered_questions[0], answer=False)
            
            return False
        
        parent_new_value: bool | None = True
        for q in self.child_questions:
            if q in qa_evidence_map:
                if qa_evidence_map[q] == False:
                    parent_new_value = False
                    break
                # else: check other values
            else:
                parent_new_value = None
                break

        if parent_new_value is not None:
            return update_qa_evidence_map(qa_evidence_map, question=self.parent_question, answer=parent_new_value)
        
        return False

    def _update_all_childs_to_positive(self, qa_evidence_map):
        updated = False
        for q in self.child_questions:
            qa_evidence_map_updated = update_qa_evidence_map(qa_evidence_map, question=q, answer=True)
            if qa_evidence_map_updated:
                updated = True
        return updated
    
@dataclass
class ContradictiveRule:
    first_question: str
    second_question: str

    def update(self, qa_evidence_map: dict[str, bool]):
        if self.first_question in qa_evidence_map:
            inferred_answer = not qa_evidence_map[self.first_question]
            updated = update_qa_evidence_map(qa_evidence_map, question=self.second_question, answer=inferred_answer)
            return updated
        
        elif self.second_question in qa_evidence_map:
            inferred_answer = not qa_evidence_map[self.second_question]
            updated = update_qa_evidence_map(qa_evidence_map, question=self.first_question, answer=inferred_answer)
            return updated
        
        return False
    
    @staticmethod
    def from_dict(data: dict[str, list[str]]):
        return ContradictiveRule(
            first_question=data["first_question"],
            second_question=data["second_question"],
        )

@dataclass
class InferenceRules:
    general_specific_rules: list[GeneralSpecificRule] = field(default_factory=list)
    and_rules: list[AndRule] = field(default_factory=list)
    contradictive_rules: list[ContradictiveRule] = field(default_factory=list)

    @staticmethod
    def load(path: str):
        with open(path) as fp:
            data = json.load(fp)
        
        general_specific_rules = [GeneralSpecificRule.from_dict(x) for x in data["general_specific"]]
        and_rules = [AndRule.from_dict(x) for x in data.get("and", [])]
        contradictive_rules = [ContradictiveRule.from_dict(x) for x in data.get("contradictive", [])]
        return InferenceRules(
            general_specific_rules=general_specific_rules,
            and_rules=and_rules,
            contradictive_rules=contradictive_rules
        )
    
    def update(self, qa_evidence_map: dict[str, bool]):
        possibly_change_in_next_iteration = True
        while possibly_change_in_next_iteration:
            possibly_change_in_next_iteration = False
            for rule in self.general_specific_rules:
                updated = rule.update(qa_evidence_map)
                if updated:
                    possibly_change_in_next_iteration = True

            for rule in self.and_rules:
                updated = rule.update(qa_evidence_map)
                if updated:
                    possibly_change_in_next_iteration = True

            for rule in self.contradictive_rules:
                updated = rule.update(qa_evidence_map)
                if updated:
                    possibly_change_in_next_iteration = True
