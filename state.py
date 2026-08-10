import random

from symptom import Symptom, SymptomProperty

class Action:
    pass

class AskSymptom(Action):
    def __init__(self, symptom: Symptom):
        self.symptom = symptom

class AskSymptomProperty(Action):
    def __init__(self, symptom_property: SymptomProperty):
        self.symptom_property = symptom_property

class AskSection(Action):
    def __init__(self, section: str):
        self.section = section

class GivePrediction(Action):
    pass

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

class Predictor:
    def is_confidence_enough(self):
        return random.random() < 0.5

class DoctorState:
    def __init__(
            self,
            symptoms: list[Symptom],
            patient_state: PatientState | None = None,
            specific_section: str | None = None,
            current_symptom: Symptom | None = None,
            no_symptom_streak: int = 0,
            need_ask_other_section: bool = True,
    ):
        self.history: list[Symptom] = []
        self.done = False

        self.symptoms = symptoms
        self.patient_state = PatientState() if patient_state is None else patient_state
        self.specific_section = specific_section
        self.current_symptom = current_symptom
        self.no_symptom_streak = no_symptom_streak
        self.need_ask_other_section = need_ask_other_section
    
    def act(self) -> Action:
        if self.current_symptom is not None:
            action = self.get_action_for_asking_new_symptom_property(self.current_symptom)
            if action is not None:
                return action

        if (
            (not self.patient_state.is_at_least_one_symptom_occured(specific_section=self.specific_section))
            or self.no_symptom_streak < 3
        ):
            action = self.get_action_for_asking_new_symptom()
            if action is not None:
                return action

        if self.need_ask_other_section or (not self.is_prediction_enough()):
            action = self.get_action_for_asking_new_section()
            if action is not None:
                return action
        
        return GivePrediction()

    def get_action_for_asking_new_symptom_property(self, symptom: Symptom):
        for symptom_property in symptom.get_properties():
            if self.patient_state.is_symptom_property_asked(symptom_property):
                return AskSymptomProperty(symptom_property)

        return None

    def get_action_for_asking_new_symptom(self):
        for symptom in self.symptoms:
            if self.specific_section is not None and symptom.get_section() != self.specific_section:
                continue

            if self.patient_state.is_symptom_asked(symptom):
                continue

            return AskSymptom(symptom)

        return None

    def get_action_for_asking_new_section(self):
        for symptom in self.symptoms:
            if symptom in self.patient_state.symptom_occurences:
                continue

            return AskSection(symptom.get_section())

        return None

    def is_prediction_enough(self):
        return self.done
