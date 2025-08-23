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

@st.cache_resource
def init_supabase():
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
    return supabase

def init_new_session():
    supabase = init_supabase()
    df = fetch_disease_symptoms_from_supabase(supabase)

    subsymptom_df_dict = {
        "Gejala": [],
        "Variasi": [],
        "AnakGejala": [],
    }
    response = (
        supabase.table("variant_free_subsymptoms")
        .select("symptom, subsymptom")
        .execute()
    )
    for x in response.data:
        gejala = x["symptom"]
        variasi = None
        anak_gejala = x["subsymptom"]

        subsymptom_df_dict["Gejala"].append(gejala)
        subsymptom_df_dict["Variasi"].append(variasi)
        subsymptom_df_dict["AnakGejala"].append(anak_gejala)

    response = (
        supabase.table("variant_specific_subsymptoms")
        .select("symptom, variant, subsymptom")
        .execute()
    )
    for x in response.data:
        gejala = x["symptom"]
        variasi = x["variant"]
        anak_gejala = x["subsymptom"]

        subsymptom_df_dict["Gejala"].append(gejala)
        subsymptom_df_dict["Variasi"].append(variasi)
        subsymptom_df_dict["AnakGejala"].append(anak_gejala)

    subsymptom_df = pd.DataFrame(subsymptom_df_dict)

    current_state = UnnamedState(df, subsymptom_df)
    st.session_state["current_state"] = current_state
    st.session_state["question_no"] = 1

    update_asked_symptom_and_answer_possibilities()

def fetch_disease_symptoms_from_supabase(supabase):
    df_dict = {
        "Id": [],
        "Penyakit": [],
        "Gejala": [],
        "Variasi": [],
        "Frekuensi": []
    }

    response = (
        supabase.table("disease_variant_free_symptoms")
        .select("id, disease_symptoms(disease, frequency), symptom")
        .execute()
    )
    for x in response.data:
        id_ = x["id"]
        penyakit = x["disease_symptoms"]["disease"]
        gejala = x["symptom"]
        variasi = None
        frekuensi = x["disease_symptoms"]["frequency"] if x["disease_symptoms"]["frequency"] else None

        df_dict["Id"].append(id_)
        df_dict["Penyakit"].append(penyakit)
        df_dict["Gejala"].append(gejala)
        df_dict["Variasi"].append(variasi)
        df_dict["Frekuensi"].append(frekuensi)

    response = (
        supabase.table("disease_variant_specific_symptoms")
        .select("id, disease_symptoms(disease, frequency), symptom, variant")
        .execute()
    )
    for x in response.data:
        id_ = x["id"]
        penyakit = x["disease_symptoms"]["disease"]
        gejala = x["symptom"]
        variasi = x["variant"]
        frekuensi = x["disease_symptoms"]["frequency"] if x["disease_symptoms"]["frequency"] else None

        df_dict["Id"].append(id_)
        df_dict["Penyakit"].append(penyakit)
        df_dict["Gejala"].append(gejala)
        df_dict["Variasi"].append(variasi)
        df_dict["Frekuensi"].append(frekuensi)
    
    df = pd.DataFrame(df_dict)
    df = df.sort_values("Id")
    return df

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

@st.dialog(f"Ubah Gejala Penyakit")
def edit_symptom(chosen_disease, symptom, old_variant, old_frequency, symptom_id):
    st.markdown(f"**{chosen_disease} - {symptom}**")

    response = (
        supabase.table("symptom_variants")
        .select("name")
        .eq("symptom", symptom)
        .execute()
    )
    variant_options = ["-"] + [x["name"] for x in response.data]
    frequency_options = ["-", "Jarang", "Kadang", "Sering", "Sangat sering"]                

    with st.form("edit_symptom_form", enter_to_submit=False, border=False):
        new_variant = st.selectbox(
            "Variasi",
            variant_options,
            accept_new_options=True,
            index=(variant_options.index(old_variant) if old_variant else 0)
        )

        new_frequency = st.selectbox(
            "Frekuensi",
            frequency_options,
            index=(frequency_options.index(old_frequency) if old_frequency else 0)
        )

        if st.form_submit_button("Simpan"):
            if new_frequency == "-":
                new_frequency = ""

            if new_variant != "-" and new_variant not in variant_options:
                (
                    supabase.table("symptom_variants")
                    .insert({
                        "symptom": symptom,
                        "name": new_variant
                    })
                    .execute()
                )

            if old_variant is None:
                if new_variant != "-":
                    (
                        supabase.table("disease_variant_free_symptoms")
                        .delete()
                        .eq("id", symptom_id)
                        .execute()
                    )

                    (
                        supabase.table("disease_variant_specific_symptoms")
                        .insert({
                            "id": symptom_id,
                            "symptom": symptom,
                            "variant": new_variant,
                        })
                        .execute()
                    )

            else:
                if new_variant == "-":
                    (
                        supabase.table("disease_variant_specific_symptoms")
                        .delete()
                        .eq("id", symptom_id)
                        .execute()
                    )

                    (
                        supabase.table("disease_variant_free_symptoms")
                        .insert({
                            "id": symptom_id,
                            "symptom": symptom,
                        })
                        .execute()
                    )
                
                else:
                    (
                        supabase.table("disease_variant_specific_symptoms")
                        .update({
                            "variant": new_variant
                        })
                        .eq("id", symptom_id)
                        .execute()
                    )

            (
                supabase.table("disease_symptoms")
                .update({
                    "frequency": new_frequency
                })
                .eq("id", symptom_id)
                .execute()
            )

            st.rerun()

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
    if "current_state" not in st.session_state:
        del st.session_state["role"]
        st.rerun()

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
            for i, (exists, variant_column, _) in enumerate(possibilities):
                label = 'Tidak' if not exists else ('Ya' if variant_column is None else variant_column)
                label = label.replace(">", "\\>")
                if st.button(label, use_container_width=True):
                    current_state.answer(asked_symptom, exists, variant_column)
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
    st.title("Ubah data")
    symptom_tab, subsymptom_tab, other_tab = st.tabs(["Gejala Penyakit", "Anak Gejala", "???"])
    if symptom_tab:
        supabase = init_supabase()
        sb_df = fetch_disease_symptoms_from_supabase(supabase)

        response = (
            supabase.table("diseases")
            .select("name")
            .execute()
        )
        diseases = [x["name"] for x in response.data]
        if len(diseases) > 0:
            # Perlu pastikan ini tidak bisa diubah kalau sedang mengubah sesuatu.
            chosen_disease = st.selectbox("Penyakit", diseases)

            sb_df = sb_df[sb_df["Penyakit"] == chosen_disease]

            symptom_column, variant_column, frequency_column, _ = st.columns([2, 2, 2, 1])
            symptom_column.markdown("**Gejala**")
            variant_column.markdown("**Variasi**")
            frequency_column.markdown("**Frekuensi**")

            for _, row in sb_df.iterrows():
                symptom = row["Gejala"]

                symptom_column, variant_column, frequency_column, edit = st.columns([2, 2, 2, 1])
                symptom_column.text(symptom)
                variant_column.text(row["Variasi"] if row["Variasi"] else "-")
                frequency_column.text(row["Frekuensi"] if row["Frekuensi"] else "-")

                if edit.button("⚙️", key=symptom, type="tertiary"):
                    edit_symptom(chosen_disease, symptom, row["Variasi"], row["Frekuensi"], row["Id"])

            # sb_df = sb_df.drop(columns=["Penyakit"])
            # sb_df["Variasi"] = sb_df["Variasi"].fillna("")
            # sb_df["Frekuensi"] = sb_df["Frekuensi"].fillna("")
            # sb_df = sb_df.reset_index(drop=True)

            # st.data_editor(sb_df, num_rows="dynamic", key="changes", hide_index=True)
            # st.write(st.session_state["changes"])

            # button_cols = st.columns(2)
            # if button_cols[0].button("Simpan", type="primary", use_container_width=True):
            #     st.toast("(Implementasi simpan di sini)")

            # if button_cols[1].button("Batal", use_container_width=True):
            #     st.toast("(Implementasi batal di sini)")
    
    else:
        st.text("Tidak ada data penyakit.")

    st.divider()

    if st.button("Keluar dari menu ubah data", type="tertiary"):
        del st.session_state["role"]
        st.rerun()
