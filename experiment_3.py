import math
import pandas as pd

df = pd.read_excel("data.xlsx", "SymptomTable")
    
FREQUENCY_PROB_MAP = {
    "Jarang":        0.10,
    "Kadang":        0.50,
    "Sering":        0.90,
    "Sangat sering": 0.99
}

def symptom_prob(disease_probs: list[float], conditional_symptom_probs: list[float]):
    result = 0.0
    denominator = 1.0
    for p, s_if_p in zip(disease_probs, conditional_symptom_probs):
        if s_if_p != -1.0:
            result += p * s_if_p
        else:
            denominator -= p
    if denominator <= 0.0:
        raise ValueError("You can't find the symptom prob if there is no disease related to this!!!!")
    
    result /= denominator
    return result

def new_disease_probs_if_yes(disease_probs: list[float], conditional_symptom_probs: list[float]):
    default_prob = symptom_prob(disease_probs, conditional_symptom_probs)
    next_disease_prob_if_yes = [(p * (s_if_p if s_if_p != -1.0 else default_prob)) for p, s_if_p in zip(disease_probs, conditional_symptom_probs)]

    sum_next_disease_prob_if_yes = sum(next_disease_prob_if_yes)
    if sum_next_disease_prob_if_yes == 0:
        raise ValueError("Impossible")

    next_disease_prob_if_yes = [x / sum_next_disease_prob_if_yes for x in next_disease_prob_if_yes]
    return next_disease_prob_if_yes

def new_disease_probs_if_no(disease_probs: list[float], conditional_symptom_probs: list[float]):
    default_prob = symptom_prob(disease_probs, conditional_symptom_probs)
    no_disease_prob = 1.0 - sum(disease_probs)
    next_disease_prob_if_no = [p * (1 - (s_if_p if s_if_p != -1.0 else default_prob)) for p, s_if_p in zip(disease_probs, conditional_symptom_probs)]
    sum_next_disease_prob_if_no = sum(next_disease_prob_if_no) + no_disease_prob
    if sum_next_disease_prob_if_no == 0:
        raise ValueError("Impossible")

    next_disease_prob_if_no = [x / sum_next_disease_prob_if_no for x in next_disease_prob_if_no]
    return next_disease_prob_if_no

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

            symptom_filter = self.df["Gejala"] == s
            filtered_df = self.df[symptom_filter]
            if filtered_df["Variasi"].isna().all():
                conditional_symptom_probs = self.get_conditional_symptom_probs(s)
                yes_prob = symptom_prob(self.disease_probs, conditional_symptom_probs)
                next_disease_prob_if_yes = new_disease_probs_if_yes(self.disease_probs, conditional_symptom_probs)
                next_disease_prob_if_no = new_disease_probs_if_no(self.disease_probs, conditional_symptom_probs)
                score = -(yes_prob * disease_entropy(next_disease_prob_if_yes) + (1 - yes_prob) * disease_entropy(next_disease_prob_if_no))
            else:
                continue
            
            results[s] = score

        return max(results.keys(), key=lambda x: results[x])

    def get_conditional_symptom_probs(self, symptom_name: str):
        conditional_symptom_probs = []
        symptom_filter = self.df["Gejala"] == symptom_name
        for d in self.disease_names:
            disease_filter = self.df["Penyakit"] == d
            filtered_df = self.df[symptom_filter & disease_filter]
            if len(filtered_df) == 0:
                conditional_symptom_probs.append(-1.0)
            else:
                frequency = filtered_df.iloc[0]["Frekuensi"]
                if not isinstance(frequency, str):
                    frequency = "Sering"

                prob = FREQUENCY_PROB_MAP[frequency]
                conditional_symptom_probs.append(prob)
        
        return conditional_symptom_probs
    
    def answer(self, symptom: str, exists: bool, variant: str | None = None):
        self.answer_history[symptom] = {
            "exists": exists,
            "variant": variant
        }

        if variant is not None:
            raise NotImplementedError
        
        conditional_symptom_probs = self.get_conditional_symptom_probs(symptom)
        if exists:
            self.disease_probs = new_disease_probs_if_yes(self.disease_probs, conditional_symptom_probs)
        else:
            self.disease_probs = new_disease_probs_if_no(self.disease_probs, conditional_symptom_probs)

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
        answer = ""
        asked_symptom = current_state.get_best_symptom_to_ask()
        print(f"Pertanyaan {question_no}")
        while answer == "":
            candidate_answer = input(f"{asked_symptom} (ya/tidak/tidak_tahu): ")
            if candidate_answer == "ya" or candidate_answer == "tidak" or candidate_answer == "tidak_tahu":
                answer = candidate_answer
            else:
                print("Tidak valid!")

        # cond_probs = [x[asked_symptom_index] for x in disease_symptom_prob]
        if answer == "ya":
            current_state.answer(asked_symptom, True)
        elif answer == "tidak":
            current_state.answer(asked_symptom, False)
        else:
            current_state.skip(asked_symptom)
        
        question_no += 1
