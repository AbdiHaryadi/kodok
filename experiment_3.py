import math
import pandas as pd

df = pd.read_excel("data.xlsx", "SymptomTable")
    
FREQUENCY_PROB_MAP = {
    "Jarang":        0.10,
    "Kadang":        0.50,
    "Sering":        0.90,
    "Sangat sering": 0.99
}

def symptom_prob(disease_probs: list[float], conditional_symptom_probs: list[float], symptom_prob_if_no_disease: float):
    result = (1 - sum(disease_probs)) * symptom_prob_if_no_disease
    denominator = 1.0
    for p, s_if_p in zip(disease_probs, conditional_symptom_probs):
        # print(p, s_if_p)
        if s_if_p != -1.0:
            result += p * s_if_p
        else:
            denominator -= p

    if denominator <= 0.0:
        raise ValueError("You can't find the symptom prob if there is no disease related to this!!!!")
    
    # input("(ENTER)")
    
    result /= denominator
    return result

def new_disease_probs(disease_probs: list[float], conditional_symptom_probs: list[float], symptom_prob_if_no_disease: float):
    default_prob = symptom_prob(disease_probs, conditional_symptom_probs, symptom_prob_if_no_disease)
    next_disease_prob_if_yes = [(p * (s_if_p if s_if_p != -1.0 else default_prob)) for p, s_if_p in zip(disease_probs, conditional_symptom_probs)]

    no_disease_prob = 1.0 - sum(disease_probs)

    sum_next_disease_prob_if_yes = sum(next_disease_prob_if_yes) + no_disease_prob * symptom_prob_if_no_disease
    if sum_next_disease_prob_if_yes == 0:
        raise ValueError("Impossible")

    next_disease_prob_if_yes = [x / sum_next_disease_prob_if_yes for x in next_disease_prob_if_yes]
    return next_disease_prob_if_yes

def disease_entropy(disease_probs: list[float]):
    no_disease_prob = 1.0 - sum(disease_probs)
    result = 0.0
    for p in disease_probs + [no_disease_prob]:
        if p > 0.0:
            result += -p * math.log(p)

    return result

class UnnamedState:
    def __init__(self, df: pd.DataFrame):
        self.df = df

        self.disease_names = df["Penyakit"].unique()
        initial_single_prob = 1 / (len(self.disease_names) + 1)
        self.disease_probs = [initial_single_prob for _ in self.disease_names]

        self.answer_history = {}

    def print_diseases(self):
        sorted_disease_and_prob = sorted([(d_name, prob) for d_name, prob in zip(self.disease_names, self.disease_probs) if prob > 0.0], key=lambda x: (-x[1], x[0].lower()))
        no_disease_prob = 1.0 - sum(self.disease_probs)
        if len(sorted_disease_and_prob) > 0:
            for d_name, prob in sorted_disease_and_prob:
                print(f"{d_name}: {prob:.6f}")
        
        if no_disease_prob > 0.0:
            print(f"Tidak ada penyakit: {no_disease_prob:.6f}" )

    def is_certain(self):
        return max(self.disease_probs) in [1.0, 0.0]
    
    def should_stop(self):
        return max(self.disease_probs) >= 0.95 or sum(self.disease_probs) <= 0.05
    
    def get_best_symptom_to_ask(self):
        symptoms = self.df["Gejala"].unique()
        results = {}

        for s in symptoms:
            if s in self.answer_history:
                continue

            possibilities = self.get_possibilities(s)

            score = 0.0
            possibility_probs = []
            entropies = []
            for exists, variant, prob_for_no_disease in possibilities:
                conditional_symptom_probs = self.get_conditional_symptom_probs_with_variant(s, exists, variant)
                possibility_probs.append(symptom_prob(self.disease_probs, conditional_symptom_probs, prob_for_no_disease))

                next_disease_prob = new_disease_probs(self.disease_probs, conditional_symptom_probs, prob_for_no_disease)
                entropy = disease_entropy(next_disease_prob)
                entropies.append(entropy)

            # input("(ENTER)")
            
            sum_possibility_probs = sum(possibility_probs)
            possibility_probs = [x / sum_possibility_probs for x in possibility_probs]

            score = -sum(x * y for x, y in zip(possibility_probs, entropies))
            
            results[s] = score

        return max(results.keys(), key=lambda x: results[x])

    def get_possibilities(self, symptom_name: str):
        symptom_filter = self.df["Gejala"] == symptom_name
        possibilities = []
        filtered_df = self.df[symptom_filter]
        if filtered_df["Variasi"].isna().all():
            possibilities = [(True, None, 0.0), (False, None, 1.0)]

        else:
            na_exists = False
            for opt_el in filtered_df["Variasi"].unique():
                if isinstance(opt_el, str):
                    possibilities.append((True, opt_el, 0.0))
                else:
                    na_exists = True

            if na_exists:
                possibilities.append((False, None, 1.0))
        
        return possibilities
    
    def get_conditional_symptom_probs_with_variant(self, symptom_name: str, exists: bool = True, variant: str | None = None):
        conditional_symptom_probs = []
        symptom_filter = self.df["Gejala"] == symptom_name
        for d in self.disease_names:
            disease_filter = self.df["Penyakit"] == d
            filtered_df = self.df[symptom_filter & disease_filter]
            if len(filtered_df) == 0:
                conditional_symptom_probs.append(-1.0)
            else:
                current_variant = filtered_df.iloc[0]["Variasi"]
                frequency = filtered_df.iloc[0]["Frekuensi"]
                if not isinstance(frequency, str):
                    frequency = "Sering"

                prob = FREQUENCY_PROB_MAP[frequency]

                if (not exists) or (isinstance(current_variant, str) and current_variant != variant):
                    prob = 1 - prob
                
                conditional_symptom_probs.append(prob)
        
        return conditional_symptom_probs
    
    def answer(self, symptom: str, exists: bool, variant: str | None = None):
        self.answer_history[symptom] = {
            "exists": exists,
            "variant": variant
        }

        conditional_symptom_probs = self.get_conditional_symptom_probs_with_variant(symptom, exists, variant)
        print(conditional_symptom_probs)
        self.disease_probs = new_disease_probs(self.disease_probs, conditional_symptom_probs, 0.0 if exists else 1.0)

    def skip(self, symptom: str):
        self.answer_history[symptom] = {
            "skip": True
        }

current_state = UnnamedState(df)

question_no = 1
stop_asking = False

while not stop_asking:
    print("---")
    print("Prediksi:")

    current_state.print_diseases()
    print("---")

    if current_state.is_certain() or current_state.should_stop():
        stop_asking = True
    else:
        answer = -1
        asked_symptom = current_state.get_best_symptom_to_ask()
        print(f"Pertanyaan {question_no}")

        possibilities = current_state.get_possibilities(asked_symptom)
        while answer == -1:
            print(asked_symptom)
            for i, (exists, variant, _) in enumerate(possibilities):
                print(f"({i + 1}) {'Tidak' if not exists else ('Ya' if variant is None else variant)}")

            print(f"({i + 2}) (lewati)")
            candidate_answer = input("Jawab: ")

            if candidate_answer.isdigit():
                candidate_answer = int(candidate_answer)
            else:
                candidate_answer = -1

            if candidate_answer >= 1 and candidate_answer <= i + 2:
                answer = candidate_answer - 1
            else:
                print("Tidak valid!")

        # cond_probs = [x[asked_symptom_index] for x in disease_symptom_prob]
        if answer < len(possibilities):
            exists, variant, _ = possibilities[answer]
            current_state.answer(asked_symptom, exists, variant)
        else:
            current_state.skip(asked_symptom)
        
        question_no += 1
