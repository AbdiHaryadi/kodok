import json
import random

import streamlit as st

from symptom import (
    BinarySymptomProperty,
    DiscreteSymptomProperty,
    Symptom,
    SymptomProperty,
)

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
                chosen_symptom = self.symptoms.pop(index)
                if chosen_symptom.get_answer() is None:
                    result = chosen_symptom

        assert result is not None
        return result

class DummySymptomManager:
    def __init__(self, symptoms: list[Symptom]):
        self.choser = SymptomChoser(symptoms)
        self.history: list[Symptom] = []
        self.specific_section: str | None = None
        self.done = False
        self.rng = random.Random()
        self.symptoms = symptoms

        unasked_sections: list[str] = []
        for symptom in symptoms:
            section = symptom.get_section()
            if section not in unasked_sections:
                unasked_sections.append(section)
        self.unasked_sections = unasked_sections

    def take_symptom_to_ask(self):
        new_symptom = self.choser.take_one(section=self.specific_section)
        self.history.append(new_symptom)
        return new_symptom

    def set_specific_section(self, new_specific_section: str | None):
        if new_specific_section is None and self.specific_section is not None:
            self.unasked_sections.remove(self.specific_section)
        self.specific_section = new_specific_section

    def get_specific_section(self):
        return self.specific_section

    def get_next_section_to_ask(self):
        next_section = self.unasked_sections[0]
        return next_section

    def set_next_section_relevance(self, relevance: bool):
        next_section = self.get_next_section_to_ask()
        if relevance:
            self.history.clear()
            self.specific_section = next_section
        else:
            for symptom in self.symptoms:
                if symptom.get_section() == next_section and symptom.get_answer() is None:
                    symptom.set_answer(False)
            self.unasked_sections.remove(next_section)
            self.done = self.rng.random() < 0.5

    def is_done(self):
        return self.done

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
    with open("sample.json") as fp:
        json_data = json.load(fp)
    st.code(json_data)

    for section_data in json_data["sections"]:
        for symptom_data in section_data["symptoms"]:
            symptom = Symptom(
                name=symptom_data["name"],
                properties=[
                    BinarySymptomProperty(
                        name=symptom_property["name"],
                        description="Contoh deskripsi",
                    ) for symptom_property in symptom_data.get("properties", [])
                ],
                section=section_data["name"]
            )
            asked_symptoms.append(symptom)
    manager = DummySymptomManager(asked_symptoms)
    st.session_state["manager"] = manager
    st.rerun()

manager: DummySymptomManager = st.session_state["manager"]
if manager.is_done():
    st.text("Done I think")
else:
    asked_symptoms: list[Symptom] = manager.history
    if len(asked_symptoms) == 0:
        manager.take_symptom_to_ask()
        st.rerun()

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

            manager.set_specific_section(None)

            section = manager.get_next_section_to_ask()
            st.text(f"Ada keluhan di \"{section}\"?")
        
            answer = None
            if st.button("Ya"):
                answer = True
            if st.button("Tidak"):
                answer = False
        
            if answer is not None:
                manager.set_next_section_relevance(answer)
                st.rerun()
