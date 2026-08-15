import json

from doctor import AskSymptom, DoctorState, GivePrediction
from symptom import BinarySymptomProperty, Symptom

if __name__ == "__main__":
    # Testing
    asked_symptoms: list[Symptom] = []
    with open("sample.json") as fp:
        json_data = json.load(fp)

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

    state = DoctorState(symptoms=asked_symptoms)
    action = state.act()
    if not isinstance(action, AskSymptom):
        raise ValueError(f"Unexpected action type: {type(action)}")

    state = action.answer(True)
    action = state.act()
    if isinstance(action, GivePrediction):
        raise ValueError(f"How???")
    print(action)
