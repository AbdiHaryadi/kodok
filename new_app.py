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
    ):
        self.name = name
        self.description = description
        self.answer: bool | None = None
        self.properties = properties
    
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

st.title("Kodok")
if "symptoms" not in st.session_state:
    first_symptom = Symptom(
        name="Batuk",
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
        ]
    )
    st.session_state["symptoms"] = [first_symptom]

def streamlit_ask_symptom_existence(symptom: Symptom):
    name = symptom.get_name()
    st.text(name)

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

current_symptom: Symptom = st.session_state["symptoms"][-1]
if (symptom_exists := current_symptom.get_answer()) is None:
    streamlit_ask_symptom_existence(current_symptom)
elif symptom_exists:
    current_properties = current_symptom.get_properties()
    for i, current_property in enumerate(current_properties):
        if current_property.get_answer() is None:
            st.header(current_symptom.get_name())
            st.progress(i / len(current_properties))
            streamlit_ask_property(current_property)
            break
    else:
        st.text("Done (all properties asked)")
else:
    st.text("Done (no symptom existence)")
