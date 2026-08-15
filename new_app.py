import json

import streamlit as st

from disease import Disease
from doctor import AskSection, AskSymptom, AskSymptomProperty, DoctorState, GivePrediction
from symptom import (
    DiscreteSymptomProperty,
    Symptom,
)

def streamlit_ask_symptom_existence(action: AskSymptom):
    symptom = action.symptom
    name = symptom.get_name()
    st.text(f"{name} (bagian: {symptom.get_section()})")

    answer = None
    if st.button("Ya"):
        answer = True
    if st.button("Tidak"):
        answer = False

    if answer is not None:
        st.session_state["state"] = action.answer(answer)
        st.rerun()

def streamlit_ask_property(action: AskSymptomProperty):
    property = action.symptom_property
    current_symptom = action.symptom
    if not isinstance(property, DiscreteSymptomProperty):
        raise NotImplementedError("Interface not supported")

    name = property.get_name()

    st.header(current_symptom.get_name())
    st.progress(action.previous_property_completed / len(current_symptom.get_properties()))
    st.text(name)
    for answer in property.get_possible_answers():
        if st.button(answer):
            st.session_state["state"] = action.answer(answer)
            st.rerun()

st.title("Kodok")
if "state" not in st.session_state:
    with open("data.json") as fp:
        json_data = json.load(fp)
    
    symptoms = [
        Symptom.from_dict(symptom_data)
        for symptom_data in json_data["symptoms"]
    ]
    diseases = [
        Disease.from_dict(disease_data)
        for disease_data in json_data["diseases"]
    ]

    state = DoctorState(symptoms=symptoms, diseases=diseases)
    st.session_state["state"] = state
    st.rerun()

state: DoctorState = st.session_state["state"]
action = state.act()

if isinstance(action, GivePrediction):
    st.text(f"Hasil prediksi:")
    for index, pred in enumerate(action.predictions):
        st.text(f"{index + 1}. {pred.name} (Tingkat: {pred.predicate})")
elif isinstance(action, AskSymptom):
    streamlit_ask_symptom_existence(action)
elif isinstance(action, AskSymptomProperty):
    streamlit_ask_property(action)
elif isinstance(action, AskSection):
    st.text(f"Ada keluhan di \"{action.section}\"?")
            
    answer = None
    if st.button("Ya"):
        answer = True
    if st.button("Tidak"):
        answer = False

    if answer is not None:
        st.session_state["state"] = action.answer(answer)
        st.rerun()
else:
    raise ValueError("Unknown action:", action)
