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


class StreamlitDiscreteSymptomPropertyAsker:
    def __init__(self, property: DiscreteSymptomProperty):
        self.property = property

        name = self.property.get_name()
        if name in st.session_state:
            self.property.set_answer(st.session_state[name])
    
    def ask(self):
        answer = self.property.get_answer()
        if answer is not None:
            return True

        name = self.property.get_name()
        st.text(name)
        for answer in self.property.get_possible_answers():
            if st.button(answer):
                st.session_state[name] = answer
                self.property.set_answer(st.session_state[name])

        return name in st.session_state

symptom = Symptom(
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

name = symptom.get_name()
if f"Symptom_{name}" in st.session_state:
    symptom.set_answer(st.session_state[f"Symptom_{name}"])

st.title("Kodok")

answer = symptom.get_answer()
if answer is None:
    st.text(name)
    if st.button("Ya"):
        answer = True
    
    if st.button("Tidak"):
        answer = False

    if answer is not None:
        st.session_state[f"Symptom_{name}"] = answer
        st.rerun()

else:
    if answer is True:
        st.header(name)

        properties = symptom.get_properties()

        print("---")
        progress = st.progress(0.0)
        for index, property in enumerate(properties):
            if not isinstance(property, DiscreteSymptomProperty):
                raise NotImplementedError("Interface not supported")
            
            asker = StreamlitDiscreteSymptomPropertyAsker(property)
            placeholder = st.empty()
            with placeholder.container():
                asked = asker.ask()

            if not asked:
                break

            progress.progress((index + 1) / len(properties))

            print(property.get_name(), property.get_answer())
            placeholder.empty()
    
    # else: have a nice day