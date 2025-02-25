from dataclasses import dataclass, field
import json

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
                if q in qa_evidence_map:
                    if qa_evidence_map[q] == False:
                        continue

                    raise ValueError(f"Contradiction detected: For {qa_evidence_map=}, it leads to contradiction in question {q}.")
                
                qa_evidence_map[q] = False
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
                if q in qa_evidence_map:
                    if qa_evidence_map[q] == True:
                        continue

                    raise ValueError(f"Contradiction detected: For {qa_evidence_map=}, it leads to contradiction in question {q}.")
                
                qa_evidence_map[q] = True
                updated = True

        return updated

@dataclass
class InferenceRules:
    general_specific_rules: list[GeneralSpecificRule] = field(default_factory=list)

    @staticmethod
    def load(path: str):
        with open(path) as fp:
            data = json.load(fp)
        
        general_specific_rules = [GeneralSpecificRule.from_dict(x) for x in data["general_specific"]]
        return InferenceRules(
            general_specific_rules=general_specific_rules
        )
    
    def update(self, qa_evidence_map: dict[str, bool]):
        possibly_changed = True
        while possibly_changed:
            possibly_changed = False
            for rule in self.general_specific_rules:
                updated = rule.update(qa_evidence_map)
                if updated:
                    possibly_changed = True
