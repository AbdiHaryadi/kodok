import json

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

total_symptom_score = 0.0
known_frequency_count = 0

FREQUENCY_PROB_MAP = {
    "jarang": 0.15,
    "kadang": 0.5,
    "sering": 0.85,
    "sangat_sering": 1.00
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
                    total_symptom_score += prob
                    known_frequency_count += 1
                    symptom_prob_list.append(prob)
                else:
                    symptom_prob_list.append(-1.0)

                break
        
        else:
            symptom_prob_list.append(0.0)

    disease_symptom_prob.append(symptom_prob_list)

default_frequency_score = total_symptom_score / known_frequency_count

for i in range(n_diseases):
    for j in range(n_symptoms):
        if disease_symptom_prob[i][j] == -1.0:
           disease_symptom_prob[i][j] = default_frequency_score 

for x in disease_symptom_prob:
    print(*(f"{y:.2f}" for y in x), sep=" ")

asked_symptoms = [False for _ in range(n_symptoms)]

stop_asking = False

disease_frequencies = [x["frequency"] for x in data]
sum_disease_frequencies = sum(disease_frequencies)
current_disease_prob = [x / (sum_disease_frequencies + 1) for x in disease_frequencies]

print(symptoms)

while not stop_asking:
    symptom_key_map: dict[int, float] = {}
    print("---")
    print("Prediksi:")

    sorted_disease_and_prob = sorted([(d_name, prob) for d_name, prob in zip(diseases, current_disease_prob) if prob > 0.0], key=lambda x: (-x[1], x[0].lower()))
    if len(sorted_disease_and_prob) > 0:
        for d_name, prob in sorted_disease_and_prob:
            print(f"{d_name}: {prob:.6f}")
    else:
        print("(kosong)")
    print("---")

    no_disease_prob = 1 - sum(current_disease_prob)
    if max(current_disease_prob) == 1.0 or no_disease_prob == 1:
        stop_asking = True
    else:
        print("---")
        for j in range(n_symptoms):
            if asked_symptoms[j]:
                continue

            next_disease_prob_if_yes = [p * disease_symptom_prob[i][j] for i, p in enumerate(current_disease_prob)]
            sum_next_disease_prob_if_yes = sum(next_disease_prob_if_yes)
            if sum_next_disease_prob_if_yes == 0:
                continue

            next_disease_prob_if_yes = [x / sum_next_disease_prob_if_yes for x in next_disease_prob_if_yes]

            next_disease_prob_if_no = [p * (1 - disease_symptom_prob[i][j]) for i, p in enumerate(current_disease_prob)]
            sum_next_disease_prob_if_no = sum(next_disease_prob_if_no) + no_disease_prob
            if sum_next_disease_prob_if_no == 0:
                continue
            next_disease_prob_if_no = [x / sum_next_disease_prob_if_no for x in next_disease_prob_if_no]

            if next_disease_prob_if_yes == next_disease_prob_if_no == current_disease_prob:
                continue  # Tidak berguna, coy.

            max_disease_prob_if_yes = max(next_disease_prob_if_yes)
            max_disease_prob_if_no = max(max(next_disease_prob_if_no), no_disease_prob / sum_next_disease_prob_if_no)
            
            symptom_key_map[j] = max_disease_prob_if_yes + max_disease_prob_if_no
            print(f"{symptoms[j]} jika ya:", max_disease_prob_if_yes)
            print(f"{symptoms[j]} jika tidak:", max_disease_prob_if_no)
            print("Total:", symptom_key_map[j])

        print("---")

        if len(symptom_key_map) == 0:
            stop_asking = True
        else:
            asked_symptom_index = max(symptom_key_map.keys(), key=lambda x: symptom_key_map[x])

            answer = ""
            while answer == "":
                candidate_answer = input(f"{symptoms[asked_symptom_index]} (ya/tidak): ")
                if candidate_answer == "ya" or candidate_answer == "tidak":
                    answer = candidate_answer
                else:
                    print("Tidak valid!")

            if answer == "ya":
                next_disease_prob_if_yes = [p * disease_symptom_prob[i][asked_symptom_index] for i, p in enumerate(current_disease_prob)]
                sum_next_disease_prob_if_yes = sum(next_disease_prob_if_yes)
                next_disease_prob_if_yes = [x / sum_next_disease_prob_if_yes for x in next_disease_prob_if_yes]
                current_disease_prob = next_disease_prob_if_yes
            else:
                next_disease_prob_if_no = [p * (1 - disease_symptom_prob[i][asked_symptom_index]) for i, p in enumerate(current_disease_prob)]
                sum_next_disease_prob_if_no = sum(next_disease_prob_if_no) + no_disease_prob
                next_disease_prob_if_no = [x / sum_next_disease_prob_if_no for x in next_disease_prob_if_no]
                current_disease_prob = next_disease_prob_if_no
            
            asked_symptoms[asked_symptom_index] = True
