import random

import streamlit as st

from symptom import (
    BinarySymptomProperty,
    DiscreteSymptomProperty,
    SymptomProperty,
)

class Symptom:
    def __init__(
            self,
            name: str,
            description: str = "",
            properties: list[SymptomProperty] = [],
            section: str = "",
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

class SymptomChoser:
    def __init__(self, symptoms: list[Symptom]) -> None:
        self.symptoms = symptoms
        self.rng = random.Random(120)

    def take_one(
            self,
            section: str | None = None
    ):
        result: Symptom | None = None
        attempt = 0
        while result is None and attempt < 500:
            attempt += 1
            index = self.rng.randint(0, len(self.symptoms) - 1)
            if section is None or self.symptoms[index].section == section:
                result = self.symptoms.pop(index)

        assert result is not None
        return result

class DummySymptomManager:
    def __init__(self, symptoms: list[Symptom]):
        self.choser = SymptomChoser(symptoms)
        self.history: list[Symptom] = []
        self.specific_section: str | None = None

    def take_symptom_to_ask(self):
        new_symptom = self.choser.take_one(section=self.specific_section)
        self.history.append(new_symptom)
        return new_symptom

    def set_specific_section(self, new_specific_section: str | None):
        self.specific_section = new_specific_section

def streamlit_ask_symptom_existence(symptom: Symptom):
    name = symptom.get_name()
    st.text(f"{name} (bagian: {symptom.get_section()})")

    answer = None
    if st.button("Ya"):
        answer = True
    if st.button("Tidak"):
        answer = False

    if answer is not None:
        symptom.set_answer(answer)
        st.rerun()

def streamlit_ask_property(property: SymptomProperty):
    if not isinstance(property, DiscreteSymptomProperty):
        raise NotImplementedError("Interface not supported")

    name = property.get_name()
    st.text(name)
    for answer in property.get_possible_answers():
        if st.button(answer):
            property.set_answer(answer)
            st.rerun()

st.title("Kodok")
if "manager" not in st.session_state:
    asked_symptoms: list[Symptom] = []
    for i in range(100):
        rng = random.Random(1000 + i)
        symptom = Symptom(
            name=f"Gejala {i + 1}",
            properties=[
                BinarySymptomProperty(
                    name="Kekambuhan",
                    description="Contoh deskripsi",
                ),
                DiscreteSymptomProperty(
                    name="Jenis batuk",
                    description="Contoh deskripsi",
                    possible_answers=["Kering", "Berdahak"]
                ),
                DiscreteSymptomProperty(
                    name="Cairan hidung & tenggorokan",
                    description="Contoh deskripsi",
                    possible_answers=["Cair & Bening", "Kental & Kuning Kehijauan"]
                )
            ],
            section=f"Bagian {rng.randint(1, 10)}"
        )
        asked_symptoms.append(symptom)
    manager = DummySymptomManager(asked_symptoms)
    manager.take_symptom_to_ask()
    st.session_state["manager"] = manager
    st.rerun()

manager: DummySymptomManager = st.session_state["manager"]
asked_symptoms: list[Symptom] = manager.history
current_symptom = asked_symptoms[-1]
if (current_symptom_exists := current_symptom.get_answer()) is None:
    streamlit_ask_symptom_existence(current_symptom)
else:
    if current_symptom_exists:
        current_properties = current_symptom.get_properties()
        for i, current_property in enumerate(current_properties):
            if current_property.get_answer() is None:
                st.header(current_symptom.get_name())
                st.progress(i / len(current_properties))
                streamlit_ask_property(current_property)
                current_symptom_completed = False
                break
        else:
            current_symptom_completed = True
    else:
        current_symptom_completed = True

    if current_symptom_completed:
        if current_symptom_exists:
            manager.set_specific_section(current_symptom.get_section())
        
        # Check if you need more symptoms.
        any_symptom_exists = any(x.get_answer() is True for x in asked_symptoms)
        if not any_symptom_exists:
            next_symptom_needed = True
        else:
            streak_to_stop = 3
            if len(asked_symptoms) < streak_to_stop:
                next_symptom_needed = True
            else:
                for current_symptom in asked_symptoms[-streak_to_stop:]:
                    if current_symptom.get_answer() is True:
                        next_symptom_needed = True
                        break
                else:
                    next_symptom_needed = False
        
        if next_symptom_needed:
            manager.take_symptom_to_ask()
            st.rerun()

        st.text("Done I think")
