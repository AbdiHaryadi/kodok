from dataclasses import dataclass, field


@dataclass
class QuestionAnswer:
    question: str
    answer: bool

@dataclass
class ObjectSpecification:
    name: str
    positive_questions: list[str] = field(default_factory=lambda: [])
    negative_questions: list[str] = field(default_factory=lambda: [])

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
