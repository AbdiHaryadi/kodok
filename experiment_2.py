import json
import math

class DiseaseProbabilities:
    def __init__(self, names: list[str], data: list[float]):
        self.names = names
        self.data = data

    def print_diseases(self):
        sorted_disease_and_prob = sorted([(d_name, prob) for d_name, prob in zip(self.names, self.data) if prob > 0.0], key=lambda x: (-x[1], x[0].lower()))
        no_disease_prob = 1.0 - sum(self.data)
        if len(sorted_disease_and_prob) > 0:
            for d_name, prob in sorted_disease_and_prob:
                print(f"{d_name}: {prob:.6f}")
        
        if no_disease_prob > 0.0:
            print(f"Tidak ada penyakit: {no_disease_prob:.6f}" )

    def transition_if_yes(self, conditional_symptom_probs: list[float]):
        default_prob = self.symptom_prob(conditional_symptom_probs)
        next_disease_prob_if_yes = [(p * (s_if_p if s_if_p != -1.0 else default_prob)) for p, s_if_p in zip(self.data, conditional_symptom_probs)]

        sum_next_disease_prob_if_yes = sum(next_disease_prob_if_yes)
        if sum_next_disease_prob_if_yes == 0:
            return None

        next_disease_prob_if_yes = [x / sum_next_disease_prob_if_yes for x in next_disease_prob_if_yes]
        return DiseaseProbabilities(self.names, next_disease_prob_if_yes)
    
    def transition_if_no(self, conditional_symptom_probs: list[float]):
        default_prob = self.symptom_prob(conditional_symptom_probs)
        no_disease_prob = 1.0 - sum(self.data)
        next_disease_prob_if_no = [p * (1 - (s_if_p if s_if_p != -1.0 else default_prob)) for p, s_if_p in zip(self.data, conditional_symptom_probs)]
        sum_next_disease_prob_if_no = sum(next_disease_prob_if_no) + no_disease_prob
        if sum_next_disease_prob_if_no == 0:
            return None

        next_disease_prob_if_no = [x / sum_next_disease_prob_if_no for x in next_disease_prob_if_no]
        return DiseaseProbabilities(self.names, next_disease_prob_if_no)
    
    def symptom_prob(self, conditional_symptom_probs: list[float]):
        result = 0.0
        denominator = 1.0
        for p, s_if_p in zip(self.data, conditional_symptom_probs):
            if s_if_p != -1.0:
                result += p * s_if_p
            else:
                denominator -= p
        if denominator <= 0.0:
            raise ValueError("You can't find the symptom prob if there is no disease related to this!!!!")
        
        result /= denominator
        return result
    
    def is_certain(self):
        return max(self.data) in [1.0, 0.0]
    
    def entropy(self):
        no_disease_prob = 1.0 - sum(self.data)
        result = 0.0
        for p in self.data + [no_disease_prob]:
            if p > 0.0:
                result += -p * math.log(p)

        return result

with open("data_3.json") as fp:
    data = json.load(fp)

diseases: list[str] = [x["name"] for x in data]
n_diseases = len(diseases)
symptoms: list[str] = []

for x in data:
    for symptom_data in x["symptoms"]:
        symptom_name = symptom_data["name"]
        if symptom_name not in symptoms:
            symptoms.append(symptom_name)

n_symptoms = len(symptoms)

disease_symptom_prob: list[list[float]] = []

FREQUENCY_PROB_MAP = {
    "tidak_ada": 0.0,
    "jarang": 0.15,
    "kadang": 0.5,
    "sering": 0.85,
    "sangat_sering": 0.99
    # "jarang": 0.25,
    # "kadang": 0.50,
    # "sering": 0.75,
    # "sangat_sering": 1.00
}
for x in data:
    symptom_prob_list: list[float] = []
    for s in symptoms:
        for symptom_data in x["symptoms"]:
            if symptom_data["name"] == s:
                if "frequency" in symptom_data:
                    prob = FREQUENCY_PROB_MAP[symptom_data["frequency"]]
                    symptom_prob_list.append(prob)
                else:
                    raise ValueError("No frequency information????")

                break
        
        else:
            symptom_prob_list.append(-1.0)  # Ini yang salah!

    disease_symptom_prob.append(symptom_prob_list)

for x in disease_symptom_prob:
    print(*(f"{y:.2f}" for y in x), sep=" ")

asked_symptoms = [False for _ in range(n_symptoms)]

stop_asking = False

disease_frequencies = [x["frequency"] for x in data]
sum_disease_frequencies = sum(disease_frequencies)
initial_disease_prob_data = [x / (sum_disease_frequencies + 1) for x in disease_frequencies]
current_disease_prob = DiseaseProbabilities(
    diseases,
    initial_disease_prob_data
)

print(symptoms)
question_no = 1

while not stop_asking:
    print("---")
    print("Prediksi:")

    current_disease_prob.print_diseases()
    print("---")

    if current_disease_prob.is_certain():
        stop_asking = True
    else:
        symptom_key_map: dict[int, float] = {}
        print("---")
        current_entropy = current_disease_prob.entropy()
        for j in range(n_symptoms):
            if asked_symptoms[j]:
                continue

            cond_probs = [x[j] for x in disease_symptom_prob]
            next_disease_prob_if_yes = current_disease_prob.transition_if_yes(cond_probs)
            if next_disease_prob_if_yes is None:
                continue

            next_disease_prob_if_no = current_disease_prob.transition_if_no(cond_probs)
            if next_disease_prob_if_no is None:
                continue

            yes_prob = current_disease_prob.symptom_prob(cond_probs)
            score = -(yes_prob * next_disease_prob_if_yes.entropy() + (1 - yes_prob) * next_disease_prob_if_no.entropy())
            symptom_key_map[j] = score

        if len(symptom_key_map) == 0:
            stop_asking = True
        else:
            asked_symptom_index = max(symptom_key_map.keys(), key=lambda x: symptom_key_map[x])

            answer = ""
            print(f"Pertanyaan {question_no}")
            while answer == "":
                candidate_answer = input(f"{symptoms[asked_symptom_index]} (ya/tidak/tidak_tahu): ")
                if candidate_answer == "ya" or candidate_answer == "tidak" or candidate_answer == "tidak_tahu":
                    answer = candidate_answer
                else:
                    print("Tidak valid!")

            cond_probs = [x[asked_symptom_index] for x in disease_symptom_prob]
            if answer == "ya":
                next_disease_prob_if_yes = current_disease_prob.transition_if_yes(cond_probs)
                assert next_disease_prob_if_yes is not None
                current_disease_prob = next_disease_prob_if_yes
            elif answer == "tidak":
                next_disease_prob_if_no = current_disease_prob.transition_if_no(cond_probs)
                assert next_disease_prob_if_no is not None
                current_disease_prob = next_disease_prob_if_no
            # else: tidak ada transisi, bro.
            
            asked_symptoms[asked_symptom_index] = True
            question_no += 1
