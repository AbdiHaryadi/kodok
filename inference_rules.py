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

            # Negative general -> negative specific
            for rule in self.general_specific_rules:
                negate_specific_questions = False
                for q in rule.general_questions:
                    if q in qa_evidence_map and (qa_evidence_map[q] == False):
                        negate_specific_questions = True
                        break

                if negate_specific_questions:
                    for q in rule.specific_questions:
                        if q in qa_evidence_map:
                            if qa_evidence_map[q] == False:
                                continue

                            raise ValueError(f"Contradiction detected: For {qa_evidence_map=}, {rule=} fired, but it leads to contradiction in question {q}.")
                        
                        qa_evidence_map[q] = False
                        possibly_changed = True

            # Positive specific -> Positive general
            for rule in self.general_specific_rules:
                satisfy_general_questions = False
                for q in rule.specific_questions:
                    if q in qa_evidence_map and (qa_evidence_map[q] == True):
                        satisfy_general_questions = True
                        break

                if satisfy_general_questions:
                    for q in rule.general_questions:
                        if q in qa_evidence_map:
                            if qa_evidence_map[q] == True:
                                continue

                            raise ValueError(f"Contradiction detected: For {qa_evidence_map=}, {rule=} fired, but it leads to contradiction in question {q}.")
                        
                        qa_evidence_map[q] = True
                        possibly_changed = True
