class SymptomProperty:
    def __init__(
            self,
            name: str,
            description: str = "",
    ):
        self.name = name
        self.description = description

    def get_name(self):
        return self.name
    
    def get_description(self):
        return self.description

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

    def is_valid_answer(self, answer: str):
        return answer in self.possible_answers
    
class BinarySymptomProperty(DiscreteSymptomProperty):
    def __init__(self, name: str, description: str = ""):
        super().__init__(
            name=name,
            description=description,
            possible_answers=["Ya", "Tidak"]
        )

def symptom_property_factory(symptom_property_data: dict):
    if "possible_answers" in symptom_property_data:
        return DiscreteSymptomProperty(
            name=symptom_property_data["name"],
            possible_answers=symptom_property_data["possible_answers"]
        )
    else:
        return BinarySymptomProperty(name=symptom_property_data["name"])

class Symptom:
    def __init__(
            self,
            name: str,
            description: str = "",
            properties: list[SymptomProperty] = [],
            section: str | None = None,
    ):
        self.name = name
        self.description = description
        self.properties = properties
        self.section = section
    
    def get_name(self):
        return self.name
    
    def get_description(self):
        return self.description

    def get_properties(self):
        return self.properties.copy()

    def get_section(self):
        return self.section

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data["name"],
            section=data.get("section", None),
            properties=[
                symptom_property_factory(property_data)
                for property_data in data.get("properties", [])
            ]
        )
