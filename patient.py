from symptom import Symptom, SymptomProperty

class PatientSymptomPropertyInfo:
    def __init__(
            self,
            name: str,
            value: str,
            subproperties: list["PatientSymptomPropertyInfo"] | None = None,
    ):
            self.name = name
            self.value = value
            self.subproperties = [] if subproperties is None else subproperties

    def copy(self):
        return PatientSymptomPropertyInfo(
            name=self.name,
            value=self.value,
            subproperties=self.subproperties.copy() 
        )

class PatientSymptomInfo:
    def __init__(
            self,
            name: str,
            value: bool = True,
            properties: list[PatientSymptomPropertyInfo] | None = None,
    ):
        self.name = name
        self.value = value
        self.properties = [] if properties is None else properties

    def copy(self):
        return PatientSymptomInfo(
            name=self.name,
            value=self.value,
            properties=[property.copy() for property in self.properties]
        )

class PatientState:
    def __init__(
            self,
            symptom_occurences: dict[Symptom, bool] | None = None,
            symptom_property_answers: dict[SymptomProperty, str] | None = None,
    ):
        self.symptom_occurences = {} if symptom_occurences is None else symptom_occurences
        self.symptom_property_answers = {} if symptom_property_answers is None else symptom_property_answers

    def is_at_least_one_symptom_occured(self, specific_section: str | None):
        for symptom, occured in self.symptom_occurences.items():
            if specific_section is not None and symptom.get_section() != specific_section:
                continue

            if occured:
                return True

        return False

    def is_symptom_asked(self, symptom: Symptom):
        return symptom in self.symptom_occurences

    def is_symptom_property_asked(self, symptom_property: SymptomProperty):
        return symptom_property in self.symptom_property_answers

    def copy(self):
        return PatientState(
            symptom_occurences=self.symptom_occurences.copy(),
            symptom_property_answers=self.symptom_property_answers.copy(),
        )

    @classmethod
    def from_string_dict(cls, symptom_occurences: dict[str, bool] | None = None):
        return cls(
            symptom_occurences={
                Symptom(name=name): occured
                for name, occured in symptom_occurences.items()
            } if symptom_occurences is not None else None
        )
