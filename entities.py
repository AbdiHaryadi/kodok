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