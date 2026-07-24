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
    def __init__(self, property: DiscreteSymptomProperty, key: str | None = None):
        self.property = property
        if key is None:
            key = f"SymptomProperty_{self.property.get_name()}"

        self.key = key
        if self.key in st.session_state:
            self.property.set_answer(st.session_state[self.key])
    
    def ask(self):
        answer = self.property.get_answer()
        if answer is not None:
            return True

        name = self.property.get_name()
        st.text(name)
        for answer in self.property.get_possible_answers():
            if st.button(answer):
                st.session_state[self.key] = answer
                self.property.set_answer(st.session_state[self.key])

        return self.key in st.session_state

class StreamlitSymptomAsker:
    def __init__(self, symptom: Symptom, key: str | None = None):
        self.symptom = symptom
        if key is None:
            key = f"Symptom_{self.symptom.get_name()}"

        self.key = key

        self.key = key
        if self.key in st.session_state:
            self.symptom.set_answer(st.session_state[self.key])
    
    def ask(self):
        answer = self.symptom.get_answer()
        placeholder = st.empty()
        if answer is None:
            with placeholder.container():
                self.ask_existence()

        answer = self.symptom.get_answer()
        if answer is None:
            return

        if answer is True:
            with placeholder.container():
                return self.ask_all_properties()
        
        return True

    def ask_existence(self):
        name = self.symptom.get_name()

        st.text(name)

        answer = None
        if st.button("Ya", key="Symptom_Ya"):
            answer = True
        if st.button("Tidak", key="Symptom_Tidak"):
            answer = False

        if answer is None:
            return False

        st.session_state[self.key] = answer
        self.symptom.set_answer(st.session_state[self.key])
        return True

    def ask_all_properties(self):
        name = self.symptom.get_name()

        st.header(name)
        
        properties = self.symptom.get_properties()

        print("---")
        progress = st.progress(0.0)

        placeholder = st.empty()
        for index, property in enumerate(properties):
            with placeholder.container():
                asked = self.ask_property(property)

            if not asked:
                return False

            progress.progress((index + 1) / len(properties))

            print(property.get_name(), property.get_answer())

        placeholder.empty()
        return True

    def ask_property(self, property: SymptomProperty):
        if not isinstance(property, DiscreteSymptomProperty):
            raise NotImplementedError("Interface not supported")

        asker = StreamlitDiscreteSymptomPropertyAsker(property)
        return asker.ask()


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

st.title("Kodok")
asker = StreamlitSymptomAsker(symptom)

placeholder = st.empty()
with placeholder.container():
    asked = asker.ask()

if asked:
    placeholder.empty()
