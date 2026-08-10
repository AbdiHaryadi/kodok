class SymptomProperty:
    def __init__(
            self,
            name: str,
            description: str = "",
    ):
        self.name = name
        self.description = description
        self.answer: str | None = None

    def get_name(self):
        return self.name
    
    def get_description(self):
        return self.description
    
    def get_answer(self):
        return self.answer
    
    def set_answer(self, answer: str):
        self.answer = answer

class DiscreteSymptomProperty(SymptomProperty):
    def __init__(
            self,
            name: str,
            possible_answers: list[str],
            description: str = "",
    ):
        super().__init__(name=name, description=description)
        self.possible_answers = possible_answers

    def get_possible_answers(self):
        return self.possible_answers.copy()
    
    def set_answer(self, answer: str):
        if answer not in self.possible_answers:
            raise ValueError("Invalid answer!")

        return super().set_answer(answer)
    
class BinarySymptomProperty(DiscreteSymptomProperty):
    def __init__(self, name: str, description: str = ""):
        super().__init__(
            name=name,
            description=description,
            possible_answers=["Ya", "Tidak"]
        )

class Symptom:
    def __init__(
            self,
            name: str,
            description: str = "",
            properties: list[SymptomProperty] = [],
            section: str = "???",
    ):
        self.name = name
        self.description = description
        self.answer: bool | None = None
        self.properties = properties
        self.section = section
    
    def get_name(self):
        return self.name
    
    def get_description(self):
        return self.description
    
    def set_answer(self, answer: bool):
        self.answer = answer

    def get_properties(self):
        return self.properties.copy()
    
    def get_answer(self):
        return self.answer

    def get_section(self):
        return self.section