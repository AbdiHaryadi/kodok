from patient import PatientState


class DiseaseSymptomPropertyInfo:
    def __init__(
            self,
            name: str,
            value: str | None = None,
            frequency: str | None = None,
            subproperties: list["DiseaseSymptomPropertyInfo"] | None = None,
    ):
            self.name = name
            self.value = value
            self.frequency = frequency
            self.subproperties = [] if subproperties is None else subproperties

class DiseaseSymptomInfo:
    def __init__(
            self,
            name: str,
            frequency: str | None = "",
            properties: list[DiseaseSymptomPropertyInfo] | None = None,
    ):
        self.name = name
        self.frequency = frequency
        self.properties = [] if properties is None else properties

    def get_frequency_score(self):
        if self.frequency is None:
            return 2

        if self.frequency == "Jarang":
            return -3

        if self.frequency == "Kadang":
            return 1
        
        if self.frequency == "Sering":
            return 3
        
        raise NotImplementedError(f"Unknown frequency score for {self.frequency}")

class Disease:
    def __init__(
            self,
            name: str,
            symptom_infos: list[DiseaseSymptomInfo],
    ):
        self.name = name
        self.symptom_infos = symptom_infos

    def give_score(self, patient_state: PatientState):
        score = 0
        for symptom_info in self.symptom_infos:
            for patient_symptom, occured in patient_state.symptom_occurences.items():
                if patient_symptom.name == symptom_info.name:
                    if occured:
                        score += symptom_info.get_frequency_score()
                        # TODO: Tangani propertinya.
                    else:
                        score -= symptom_info.get_frequency_score()
                    break

        return score

sample_disease = Disease(
    name="Common Cold (Batuk Pilek)",
    symptom_infos=[
        DiseaseSymptomInfo(
            name="Nyeri kepala",
            frequency="Kadang",
            properties=[
                DiseaseSymptomPropertyInfo(
                    name="Tingkat",
                    value="Ringan",
                ),
            ]
        ),
        DiseaseSymptomInfo(
            name="Mata gatal",
            frequency="Sering",
        ),
        DiseaseSymptomInfo(
            name="Mata berair",
            frequency="Sering",
        ),
        DiseaseSymptomInfo(
            name="Batuk",
            properties=[
                DiseaseSymptomPropertyInfo(
                    name="Durasi",
                    value="< 7 hari"
                ),
                DiseaseSymptomPropertyInfo(
                    name="Kekambuhan",
                    frequency="Jarang",
                ),
                DiseaseSymptomPropertyInfo(
                    name="Jenis",
                    value="Kering",
                    frequency="Jarang",
                ),
                DiseaseSymptomPropertyInfo(
                    name="Jenis",
                    value="Berdahak",
                    frequency="Jarang",
                ),
            ]
        ),
        DiseaseSymptomInfo(
            name="Nyeri tenggorokan",
            frequency="Sering",
        ),
        DiseaseSymptomInfo(
            name="Suara serak",
            frequency="Jarang",
        ),
        DiseaseSymptomInfo(
            name="Hidung tersumbat",
            frequency="Sering",
        ),
        DiseaseSymptomInfo(
            name="Hidung berair",
            frequency="Sering",
        ),
        DiseaseSymptomInfo(
            name="Cairan hidung dan tenggorokan",
            properties=[
                DiseaseSymptomPropertyInfo(
                    name="Cair/Kental",
                    value="Cair"
                ),
                DiseaseSymptomPropertyInfo(
                    name="Warna",
                    value="bening"
                ),
            ],
        ),
        DiseaseSymptomInfo(
            name="Bersin",
            frequency="Sering",
        ),
        DiseaseSymptomInfo(
            name="Nyeri menelan",
            frequency="Jarang",
        ),
        DiseaseSymptomInfo(
            name="Sesak napas",
            frequency="Jarang",
        ),
    ]
)

if __name__ == "__main__":
    patient_state = PatientState.from_string_dict(symptom_occurences={
        "Nyeri kepala": True,
        "Mata gatal": False,
    })
    print(sample_disease.give_score(patient_state))
