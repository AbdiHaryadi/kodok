import streamlit as st
import pandas as pd
from supabase import create_client, Client
import time
from experiment_3 import UnnamedState

def to_proper_decimal_string(float_data):
    x = f"{float_data:.6f}".replace(".", ",")
    return x

def to_proper_percentage_string(float_data):
    x = f"{float_data * 100:.1f}%".replace(".", ",")
    return x

def update_asked_symptom_and_answer_possibilities():
    current_state = st.session_state["current_state"]
    asked_symptom = current_state.get_best_symptom_to_ask()
    st.session_state["asked_symptom"] = asked_symptom

    # Choose possibilities
    if asked_symptom is not None and st.session_state["question_no"] <= 10:
        possibilities = current_state.get_possibilities(asked_symptom)
    else:
        possibilities = []
    st.session_state["possibilities"] = possibilities

def next_question():
    st.session_state["question_no"] = st.session_state["question_no"] + 1
    update_asked_symptom_and_answer_possibilities()

def init_new_session():
    data_path = st.secrets["DATA_PATH"]
    df = pd.read_excel(data_path, "SymptomTable")
    subsymptom_df = pd.read_excel(data_path, "SubsymptomTable")

    current_state = UnnamedState(df, subsymptom_df)
    st.session_state["current_state"] = current_state
    st.session_state["question_no"] = 1

    update_asked_symptom_and_answer_possibilities()

@st.cache_resource
def init_supabase():
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
    return supabase

@st.dialog("Ubah data")
def ask_password():
    with st.form("pass_form", enter_to_submit=False, border=False):
        password = st.text_input("Kata sandi", type="password")
        if st.form_submit_button("Masuk"):
            start_time = time.time()
            password_correct = (password == st.secrets["ADMIN_PASS"])
            delay = time.time() + 1 - start_time
            if delay > 0:
                time.sleep(delay)

            if password_correct:
                st.session_state["role"] = "admin"
                st.rerun()
            else:
                st.toast("Kata sandi salah.", icon="❌")

if "role" not in st.session_state:
    if "debug_mode" not in st.session_state:
        st.session_state["debug_mode"] = False
    
    if st.button("Mulai", type="primary"):
        st.session_state["role"] = "user"
        init_new_session()
        st.rerun()

    new_value = st.checkbox("Mode awakutu", value=st.session_state["debug_mode"])
    st.session_state["debug_mode"] = new_value

    st.divider()

    if st.button("Ubah data", type="tertiary"):
        ask_password()

elif st.session_state["role"] == "user":
    current_state = st.session_state["current_state"]

    possibilities = st.session_state["possibilities"]

    if st.session_state["debug_mode"]:
        conversation_view, right_view = st.columns(2)
    else:
        conversation_view = st.container()
        right_view = None

    if len(possibilities) > 0:
        question_no = st.session_state["question_no"]
        asked_symptom = st.session_state["asked_symptom"]

        conversation_view.markdown(f"**Pertanyaan {question_no}**: {asked_symptom}")

        with conversation_view.container():
            for i, (exists, variant, _) in enumerate(possibilities):
                label = 'Tidak' if not exists else ('Ya' if variant is None else variant)
                label = label.replace(">", "\\>")
                if st.button(label, use_container_width=True):
                    current_state.answer(asked_symptom, exists, variant)
                    next_question()
                    st.rerun()

        if conversation_view.button("Lewati", type="tertiary"):
            current_state.skip(asked_symptom)
            next_question()
            st.rerun()

    else:
        conversation_view.markdown("Sesi selesai.")
        if right_view is None:
            predictions = current_state.get_predictions()
            diseases = predictions["diseases"]
            prediction_content = "**Prediksi**:"

            prediction_exists = False
            for i, p in enumerate(diseases):
                prob = p["prob"]
                if i == 0 and prob < 1/1000:
                    break

                if i == 3:
                    break

                d_name = p["name"]
                prediction_exists = True
                prob = to_proper_percentage_string(prob)
                prediction_content += f"\n- {d_name}: {prob}"

            if not prediction_exists:
                prediction_content += " (kosong)"
            
            conversation_view.markdown(prediction_content)

    # sample_df = pd.DataFrame({
    #     "Penyakit": [
    #         "Bronkitis Akut",
    #         "Common Cold",
    #         "Influenza"
    #     ],
    #     "Nilai": [
    #         0.2,
    #         0.1,
    #         0.05
    #     ]
    # })
    # right_view.bar_chart(sample_df, y="Nilai", x="Penyakit", horizontal=True)

    if right_view is not None:
        predictions = current_state.get_predictions()
        diseases = predictions["diseases"]
        right_view_content = "**Prediksi**:"

        prediction_exists = False
        for p in diseases:
            d_name = p["name"]
            prob = p["prob"]
            if prob < 1 / 100 and len(possibilities) > 0:
                break

            prediction_exists = True
            prob = to_proper_percentage_string(prob)
            right_view_content += f"\n- {d_name}: {prob}"

        if not prediction_exists:
            right_view_content += " (kosong)"


        right_view.markdown(right_view_content)

        no_disease_prob = predictions["no_disease_prob"]
        if no_disease_prob >= 1 / 100:
            no_disease_prob = to_proper_percentage_string(no_disease_prob)
            right_view.markdown(f":gray[**Tidak ada penyakit**: {no_disease_prob}]")

    # print(predictions)
    # entropy = predictions["entropy"]
    # right_view.markdown(f":gray[**Entropi**: {entropy}]")

    st.divider()
    if st.button("Mulai Ulang", use_container_width=True, type="tertiary"):
        init_new_session()
        st.rerun()

else:
    supabase = init_supabase()
    response = (
        supabase.table("disease_symptoms")
        .select("disease", "symptom", "variant", "frequency")
        .execute()
    )

    sb_df = pd.DataFrame(response.data)

    st.title("Ubah data")
    symptom_tab, subsymptom_tab, other_tab = st.tabs(["Gejala Penyakit", "Anak Gejala", "???"])
    if symptom_tab:
        st.data_editor(sb_df, num_rows="dynamic", key="changes")
        st.write(st.session_state["changes"])

        button_cols = st.columns(2)
        if button_cols[0].button("Simpan", type="primary", use_container_width=True):
            st.toast("(Implementasi simpan di sini)")

        if button_cols[1].button("Batal", use_container_width=True):
            st.toast("(Implementasi batal di sini)")

    st.divider()

    if st.button("Keluar dari menu ubah data", type="tertiary"):
        del st.session_state["role"]
        st.rerun()
