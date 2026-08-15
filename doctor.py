from disease import Disease
from patient import PatientState
from symptom import Symptom, SymptomProperty


class Action:
    pass

class DiseasePrediction:
    def __init__(self, name: str, predicate: str):
        self.name = name
        self.predicate = predicate

class DoctorState:
    def __init__(
            self,
            symptoms: list[Symptom],
            diseases: list[Disease] | None = None,
            patient_state: PatientState | None = None,
            specific_section: str | None = None,
            current_symptom: Symptom | None = None,
            no_symptom_streak: int = 0,
            need_ask_other_section: bool = True,
    ):
        self.history: list[Symptom] = []
        self.done = False

        self.symptoms = symptoms
        self.diseases = [] if diseases is None else diseases
        self.patient_state = PatientState() if patient_state is None else patient_state
        self.specific_section = specific_section
        self.current_symptom = current_symptom
        self.no_symptom_streak = no_symptom_streak
        self.need_ask_other_section = need_ask_other_section

    def act_based_on_flowchart(self, ignore_specific_section: bool = False) -> Action | None:
        if self.current_symptom is not None:
            action = self.get_action_for_asking_new_symptom_property(self.current_symptom)
            if action is not None:
                return action

        if (
            (not self.patient_state.is_at_least_one_symptom_occured(specific_section=self.specific_section))
            or self.no_symptom_streak < 3
        ):
            return self.get_action_for_asking_new_symptom(ignore_specific_section=ignore_specific_section)

        if self.need_ask_other_section or (not self.is_prediction_enough()):
            return self.get_action_for_asking_new_section()
        
        return self.get_action_for_giving_prediction()

    def get_action_for_giving_prediction(self):
        print(self.diseases)
        chosen_prediction = self.diseases[0]
        return GivePrediction([DiseasePrediction(
            name=chosen_prediction.name,
            predicate="(TBA)"
        )])
    
    def act(self) -> Action:
        action = self.act_based_on_flowchart()
        if action is None:
            action = self.act_based_on_flowchart(ignore_specific_section=True)
            if action is not None:
                print("Warning: Action found by ignoring specific section.")
        if action is None:
            action = self.get_action_for_giving_prediction()

        return action

    def get_action_for_asking_new_symptom_property(self, symptom: Symptom):
        for i, symptom_property in enumerate(symptom.get_properties()):
            if not self.patient_state.is_symptom_property_asked(symptom_property):
                return AskSymptomProperty(self, symptom, symptom_property, previous_property_completed=i)

        return None

    def get_action_for_asking_new_symptom(self, ignore_specific_section: bool = False):
        for symptom in self.symptoms:
            if (
                (not ignore_specific_section)
                and self.specific_section is not None
                and symptom.get_section() != self.specific_section
            ):
                continue

            if self.patient_state.is_symptom_asked(symptom):
                continue

            if ignore_specific_section:
                print("Warning: Asking unasked, but not related to specific section.")

            return AskSymptom(self, symptom)

        return None

    def get_action_for_asking_new_section(self):
        for symptom in self.symptoms:
            if symptom in self.patient_state.symptom_occurences:
                continue

            return AskSection(self, symptom.get_section())

        return None

    def is_prediction_enough(self):
        return self.done

    def copy(self):
        return DoctorState(
            symptoms=self.symptoms.copy(),
            diseases=self.diseases.copy(),
            patient_state=self.patient_state.copy(),
            specific_section=self.specific_section,
            current_symptom=self.current_symptom,
            no_symptom_streak=self.no_symptom_streak,
            need_ask_other_section=self.need_ask_other_section,
        )

class AskSymptom(Action):
    def __init__(self, state: DoctorState, symptom: Symptom):
        self.state = state
        self.symptom = symptom

    def answer(self, exists: bool) -> DoctorState:
        new_state = self.state.copy()
        new_state.patient_state.symptom_occurences[self.symptom] = exists
        if exists:
            new_state.specific_section = self.symptom.get_section()
            new_state.current_symptom = self.symptom
            new_state.no_symptom_streak = 0
        else:
            new_state.no_symptom_streak += 1

        return new_state

class AskSection(Action):
    def __init__(self, state: DoctorState, section: str):
        self.state = state
        self.section = section

    def answer(self, exists_symptom_in_this_section: bool) -> DoctorState:
        new_state = self.state.copy()
        if exists_symptom_in_this_section:
            new_state.specific_section = self.section
            new_state.current_symptom = None
            new_state.no_symptom_streak = 0
            new_state.need_ask_other_section = True
        else:
            for symptom in self.state.symptoms:
                if symptom.get_section() == self.section:
                    new_state.patient_state.symptom_occurences[symptom] = False
            
            new_state.need_ask_other_section = False

        return new_state

class AskSymptomProperty(Action):
    def __init__(
            self,
            state: DoctorState,
            symptom: Symptom,
            symptom_property: SymptomProperty,
            previous_property_completed: int = 0,
    ):
        self.state = state
        self.symptom = symptom
        self.symptom_property = symptom_property
        self.previous_property_completed = previous_property_completed

    def answer(self, value: str):
        new_state = self.state.copy()
        new_state.patient_state.symptom_property_answers[self.symptom_property] = value
        return new_state

class GivePrediction(Action):
    def __init__(self, predictions: list[DiseasePrediction]):
        self.predictions = predictions
