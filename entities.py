from dataclasses import dataclass, field
from typing import Callable

from inference_rules import GeneralSpecificRule


@dataclass
class QuestionAnswer:
    question: str
    answer: bool

@dataclass
class ObjectSpecification:
    name: str
    positive_questions: list[str] = field(default_factory=lambda: [])
    negative_questions: list[str] = field(default_factory=lambda: [])

    def add_general_questions(self, general_specific_rules: list[GeneralSpecificRule]):
        possibly_updated_in_next_iteration = True
        while possibly_updated_in_next_iteration:
            possibly_updated_in_next_iteration = False
            for rule in general_specific_rules:
                if any(x in rule.specific_questions for x in self.positive_questions):
                    for q in rule.general_questions:
                        if q not in self.positive_questions:
                            self.positive_questions.append(q)
                            possibly_updated_in_next_iteration = True

class ObjectSpecificationList:
    def __init__(self, data: list[ObjectSpecification]):
        self.data = data
        self.n = len(data)
        self._validate_data()

    def _validate_data(self):
        if self.n == 0:
            raise ValueError("Object specification list is empty")
        
        object_name_set: set[str] = set()
        for obj_spec in self.data:
            obj_name = obj_spec.name
            if obj_name in object_name_set:
                raise ValueError(f"Duplicate object specification with name \"{obj_name}\"")
            
            if len(obj_spec.positive_questions) == 0:
                raise ValueError(f"No positive question for object specification with name \"{obj_name}\"")
            
            object_name_set.add(obj_name)

    def __len__(self):
        return self.n
    
    def __getitem__(self, i: int):
        return self.data[i]
    
    def add_general_questions(self, general_specific_rules: list[GeneralSpecificRule]):
        for object_spec in self.data:
            object_spec.add_general_questions(general_specific_rules)

class Question:
    def __init__(self, value: str):
        self.value = value
        self.callbacks: list[Callable[[bool], None]] = []

    def add_callback(self, callback: Callable[[bool], None]):
        self.callbacks.append(callback)

    def answer(self, value: bool):
        for callback in self.callbacks:
            callback(value)
