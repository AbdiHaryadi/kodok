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
        .select("subsymptom", "parent")
        .execute()
    )
    for x in response.data:
        gejala = x["parent"]
        variasi = None
        anak_gejala = x["subsymptom"]

        subsymptom_df_dict["Gejala"].append(gejala)
        subsymptom_df_dict["Variasi"].append(variasi)
        subsymptom_df_dict["AnakGejala"].append(anak_gejala)

    response = (
        supabase.table("variant_specific_subsymptoms")
        .select("subsymptom", "parent", "parent_variant")
        .execute()
    )
    for x in response.data:
        gejala = x["parent"]
        variasi = x["parent_variant"]
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
def edit_disease_symptom(chosen_disease, symptom, old_variant, old_frequency, symptom_id):
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

@st.dialog(f"Tambah Gejala Penyakit")
def add_disease_symptom(chosen_disease):
    st.markdown(f"**Penyakit: {chosen_disease}**")

    existing_symptoms = set()

    response = (
        supabase.table("disease_variant_free_symptoms")
        .select("symptom, disease_symptoms!inner(disease)")
        .eq("disease_symptoms.disease", chosen_disease)
        .execute()
    )
    for x in response.data:
        existing_symptoms.add(x["symptom"])

    response = (
        supabase.table("disease_variant_specific_symptoms")
        .select("symptom, disease_symptoms!inner(disease)")
        .eq("disease_symptoms.disease", chosen_disease)
        .execute()
    )
    for x in response.data:
        existing_symptoms.add(x["symptom"])
    
    reusable_symptoms = set()
    
    response = (
        supabase.table("symptoms")
        .select("name")
        .execute()
    )

    for x in response.data:
        if x["name"] not in existing_symptoms:
            reusable_symptoms.add(x["name"])

    reusable_symptoms = sorted(list(reusable_symptoms))

    # with st.form("add_symptom_form", enter_to_submit=False, border=False):
    # TODO: Remove accept_new_options
    new_symptom = st.selectbox("Gejala", reusable_symptoms, index=None, accept_new_options=True)

    new_variant = None
    variant_options = ["-"]
    if new_symptom in existing_symptoms:
        st.warning("Gejala tersebut sudah ada sebelumnya.")
    elif new_symptom is not None:
        response = (
            supabase.table("symptom_variants")
            .select("name")
            .eq("symptom", new_symptom)
            .execute()
        )

        variant_options = ["-"] + [x["name"] for x in response.data]
        frequency_options = ["-", "Jarang", "Kadang", "Sering", "Sangat sering"]                

        new_variant = st.selectbox(
            "Variasi",
            variant_options,
            accept_new_options=True
        )

        new_frequency = st.selectbox(
            "Frekuensi",
            frequency_options
        )
    
    if st.button("Simpan", disabled=(new_variant is None)):
        if new_symptom not in reusable_symptoms:
            (
                supabase.table("symptoms")
                .insert({
                    "name": new_symptom
                })
                .execute()
            )

        if new_variant != "-" and new_variant not in variant_options:
            (
                supabase.table("symptom_variants")
                .insert({
                    "symptom": new_symptom,
                    "name": new_variant
                })
                .execute()
            )

        (
            supabase.table("disease_symptoms")
            .insert({
                "disease": chosen_disease,
                "frequency": new_frequency,
            })
            .execute()
        )

        response = (
            supabase.table("disease_symptoms")
            .select("id")
            .eq("disease", chosen_disease)
            .eq("frequency", new_frequency)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        new_id = response.data[0]["id"]

        if new_variant == "-":
            (
                supabase.table("disease_variant_free_symptoms")
                .insert({
                    "id": new_id,
                    "symptom": new_symptom,
                })
                .execute()
            )
        else:
            (
                supabase.table("disease_variant_specific_symptoms")
                .insert({
                    "id": new_id,
                    "symptom": new_symptom,
                    "variant": new_variant
                })
                .execute()
            )
        
        st.rerun()

@st.dialog(f"Hapus Gejala Penyakit")
def delete_disease_symptom(chosen_disease, symptom, symptom_id):
    st.markdown(f"**Hapus gejala {symptom} dari penyakit {chosen_disease}?**")        

    with st.form("delete_symptom_form", enter_to_submit=False, border=False):
        if st.form_submit_button("Ya"):
            (
                supabase.table("disease_symptoms")
                .delete()
                .eq("id", symptom_id)
                .execute()
            )
            st.rerun()

@st.dialog("Tambah Penyakit")
def add_disease():
    with st.form("add_disease_form", enter_to_submit=False, border=False):
        disease_name = st.text_input("Nama")
        disease_description = st.text_area("Deskripsi (opsional)")

        if st.form_submit_button("Tambah"):
            disease_name = disease_name.strip()
            if disease_name == "":
                st.error("Nama tidak boleh kosong.")
            else:
                existing_data = (
                    supabase.table("diseases")
                    .select("name")
                    .eq("name", disease_name)
                    .execute()
                )
                if len(existing_data.data) > 0:
                    st.error(f"Penyakit dengan nama \"{disease_name}\" sudah ada.")
                else:
                    disease_description = disease_description.strip()
                    if disease_description == "-":
                        disease_description = ""
                    
                    (
                        supabase.table("diseases")
                        .insert({
                            "name": disease_name,
                            "description": disease_description
                        })
                        .execute()
                    )
                    st.rerun()

@st.dialog("Ubah Penyakit")
def edit_disease(old_name, old_description):
    st.markdown(f"**Penyakit: {old_name}**")
    with st.form("edit_disease_form", enter_to_submit=False, border=False):
        disease_name = st.text_input("Nama", value=old_name)
        disease_description = st.text_area("Deskripsi (opsional)", value=old_description)

        if st.form_submit_button("Ubah"):
            disease_name = disease_name.strip()
            if disease_name == "":
                st.error("Nama tidak boleh kosong.")
            else:
                disease_description = disease_description.strip()
                if disease_description == "-":
                    disease_description = ""
                
                if disease_name != old_name:
                    existing_data = (
                        supabase.table("diseases")
                        .select("name")
                        .eq("name", disease_name)
                        .execute()
                    )
                    if len(existing_data.data) > 0:
                        st.error(f"Penyakit dengan nama \"{disease_name}\" sudah ada.")
                    else:
                        (
                            supabase.table("diseases")
                            .update({
                                "name": disease_name,
                                "description": disease_description
                            })
                            .eq("name", old_name)
                            .execute()
                        )
                        st.rerun()

                else:
                    (
                        supabase.table("diseases")
                        .update({
                            "description": disease_description
                        })
                        .eq("name", old_name)
                        .execute()
                    )
                    st.rerun()

@st.dialog(f"Hapus Penyakit")
def delete_disease(disease_name):
    st.markdown(f"**Hapus penyakit {disease_name}?**")        

    with st.form("delete_disease_form", enter_to_submit=False, border=False):
        if st.form_submit_button("Ya"):
            (
                supabase.table("diseases")
                .delete()
                .eq("name", disease_name)
                .execute()
            )
            st.rerun()

@st.dialog("Tambah Gejala")
def add_symptom():
    with st.form("add_symptom_form", enter_to_submit=False, border=False):
        symptom_name = st.text_input("Nama")
        symptom_description = st.text_area("Deskripsi (opsional)")

        if st.form_submit_button("Tambah"):
            symptom_name = symptom_name.strip()
            if symptom_name == "":
                st.error("Nama tidak boleh kosong.")
            else:
                existing_data = (
                    supabase.table("symptoms")
                    .select("name")
                    .eq("name", symptom_name)
                    .execute()
                )
                if len(existing_data.data) > 0:
                    st.error(f"Gejala dengan nama \"{symptom_name}\" sudah ada.")
                else:
                    symptom_description = symptom_description.strip()
                    if symptom_description == "-":
                        symptom_description = ""
                    
                    (
                        supabase.table("symptoms")
                        .insert({
                            "name": symptom_name,
                            "description": symptom_description
                        })
                        .execute()
                    )
                    st.rerun()

@st.dialog("Ubah Gejala")
def edit_symptom(old_name, old_description):
    st.markdown(f"**Gejala: {old_name}**")
    with st.form("edit_symptom_form", enter_to_submit=False, border=False):
        symptom_name = st.text_input("Nama", value=old_name)
        symptom_description = st.text_area("Deskripsi (opsional)", value=old_description)

        if st.form_submit_button("Ubah"):
            symptom_name = symptom_name.strip()
            if symptom_name == "":
                st.error("Nama tidak boleh kosong.")
            else:
                symptom_description = symptom_description.strip()
                if symptom_description == "-":
                    symptom_description = ""
                
                if symptom_name != old_name:
                    existing_data = (
                        supabase.table("symptoms")
                        .select("name")
                        .eq("name", symptom_name)
                        .execute()
                    )
                    if len(existing_data.data) > 0:
                        st.error(f"Gejala dengan nama \"{symptom_name}\" sudah ada.")
                    else:
                        (
                            supabase.table("symptoms")
                            .update({
                                "name": symptom_name,
                                "description": symptom_description
                            })
                            .eq("name", old_name)
                            .execute()
                        )
                        st.rerun()

                else:
                    (
                        supabase.table("symptoms")
                        .update({
                            "description": symptom_description
                        })
                        .eq("name", old_name)
                        .execute()
                    )
                    st.rerun()

@st.dialog(f"Hapus Gejala")
def delete_symptom(symptom_name):
    st.markdown(f"**Hapus gejala {symptom_name}?**")        

    with st.form("delete_symptom_form", enter_to_submit=False, border=False):
        if st.form_submit_button("Ya"):
            (
                supabase.table("symptoms")
                .delete()
                .eq("name", symptom_name)
                .execute()
            )
            st.rerun()

@st.dialog("Tambah Anak Gejala")
def add_subsymptom(symptom, existing_subsymptoms):
    response = (
        supabase.table("symptom_variants")
        .select("name")
        .eq("symptom", symptom)
        .execute()
    )
    variant_options = ["-"] + [x["name"] for x in response.data]

    response = (
        supabase.table("symptoms")
        .select("name")
        .execute()
    )
    subsymptom_options = []
    for x in response.data:
        if x["name"] != symptom and x["name"] not in existing_subsymptoms:
            subsymptom_options.append(x["name"])

    with st.form("add_subsymptom_form", enter_to_submit=False, border=False):
        variant = st.selectbox("Variasi", variant_options)
        subsymptom = st.selectbox("Anak gejala", subsymptom_options, index=None)

        if st.form_submit_button("Tambah"):
            # TODO: Check if this is valid to add.
            (
                supabase.table("subsymptoms")
                .insert({
                    "subsymptom": subsymptom
                })
                .execute()
            )

            response = (
                supabase.table("subsymptoms")
                .select("id")
                .eq("subsymptom", subsymptom)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            new_id = response.data[0]["id"]

            if variant == "-":
                (
                    supabase.table("variant_free_subsymptoms")
                    .insert({
                        "id": new_id,
                        "symptom": symptom
                    })
                    .execute()
                )
            else:
                (
                    supabase.table("variant_specific_subsymptoms")
                    .insert({
                        "id": new_id,
                        "symptom": symptom,
                        "variant": variant
                    })
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

        left, right = conversation_view.columns([0.9, 0.1])

        left.markdown(f"**Pertanyaan {question_no}**: {asked_symptom}")
        if right.button("❓", use_container_width=True, type="tertiary"):
            @st.dialog("Keterangan")
            def popup():
                st.text("Keterangan di sini")

            popup()

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
    disease_list_tab, symptom_list_tab, subsymptom_list_tab, disease_symptom_tab = st.tabs([
        "Daftar Penyakit",
        "Daftar Gejala",
        "Daftar Anak Gejala",
        "Gejala Penyakit"
    ])

    supabase = init_supabase()

    with disease_list_tab:
        response = (
            supabase.table("diseases")
            .select("name", "description")
            .execute()
        )
        if len(response.data) > 0:
            layout = [4, 8, 1, 1]
            name_column, description_column, _, _ = st.columns(layout)
            name_column.markdown("**Nama**")
            description_column.markdown("**Deskripsi**")

            for x in response.data:
                name_column, description_column, edit_column, del_column = st.columns(layout)
                disease_name = x["name"]
                description = x["description"]

                name_column.text(disease_name)
                description_column.text(description if description != "" else "-")

                if edit_column.button("⚙️", key=f"disease_{disease_name}_edit", type="tertiary"):
                    edit_disease(disease_name, description)

                if del_column.button("🗑️", key=f"disease_{disease_name}_delete", type="tertiary"):
                    delete_disease(disease_name)
                
            
        else:
            st.info("Tidak ada data penyakit.")

        if st.button("Tambah penyakit"):
            add_disease()

    with symptom_list_tab:
        response = (
            supabase.table("symptoms")
            .select("name", "description")
            .execute()
        )
        if len(response.data) > 0:
            layout = [4, 8, 1, 1]
            name_column, description_column, _, _ = st.columns(layout)
            name_column.markdown("**Nama**")
            description_column.markdown("**Deskripsi**")

            for x in response.data:
                name_column, description_column, edit_column, del_column = st.columns(layout)
                symptom_name = x["name"]
                description = x["description"]

                name_column.text(symptom_name)
                description_column.text(description if description != "" else "-")

                if edit_column.button("⚙️", key=f"symptom_{symptom_name}_edit", type="tertiary"):
                    edit_symptom(symptom_name, description)

                if del_column.button("🗑️", key=f"symptom_{symptom_name}_delete", type="tertiary"):
                    delete_symptom(symptom_name)
            
        else:
            st.info("Tidak ada data gejala.")

        if st.button("Tambah gejala"):
            add_symptom()

    with subsymptom_list_tab:
        response = (
            supabase.table("symptoms")
            .select("name")
            .execute()
        )
        symptoms = [x["name"] for x in response.data]

        if len(symptoms) > 0:
            chosen_symptom = st.selectbox("Gejala", symptoms, key="chosen_symptom")

            view_data = []
            response = (
                supabase.table("variant_free_subsymptoms")
                .select("id", "subsymptoms(subsymptom)")
                .eq("symptom", chosen_symptom)
                .execute()
            )
            for x in response.data:
                view_data.append((x["id"], "-", x["subsymptoms"]["subsymptom"]))

            response = (
                supabase.table("variant_specific_subsymptoms")
                .select("id", "variant", "subsymptoms(subsymptom)")
                .eq("symptom", chosen_symptom)
                .execute()
            )
            
            for x in response.data:
                view_data.append((x["id"], x["variant"], x["subsymptoms"]["subsymptom"]))
            
            view_data.sort(key=lambda x: x[0])

            layout = [3, 9, 1, 1]
            variant_column, subsymptom_column, _, _ = st.columns(layout)
            variant_column.markdown("**Variasi**")
            subsymptom_column.markdown("**Anak Gejala**")

            for _, variant, subsymptom in view_data:
                variant_column, subsymptom_column, edit_column, del_column = st.columns(layout)
                variant_column.text(variant)
                subsymptom_column.text(subsymptom)

                if edit_column.button("⚙️", key=f"subsymptom_{subsymptom}_edit", type="tertiary"):
                    pass

                if del_column.button("🗑️", key=f"subsymptom_{subsymptom}_delete", type="tertiary"):
                    pass

            if st.button("Tambah anak gejala"):
                existing_subsymptoms = [subsymptom for _, _, subsymptom in view_data]
                add_subsymptom(chosen_symptom, existing_subsymptoms)
            
        else:
            st.info("Tidak ada data gejala.")

    with disease_symptom_tab:
        sb_df = fetch_disease_symptoms_from_supabase(supabase)

        response = (
            supabase.table("diseases")
            .select("name")
            .execute()
        )
        diseases = [x["name"] for x in response.data]
        if len(diseases) > 0:
            chosen_disease = st.selectbox("Penyakit", diseases, key="chosen_disease")

            sb_df = sb_df[sb_df["Penyakit"] == chosen_disease]

            symptom_column, variant_column, frequency_column, _, _ = st.columns([4, 4, 4, 1, 1])
            symptom_column.markdown("**Gejala**")
            variant_column.markdown("**Variasi**")
            frequency_column.markdown("**Frekuensi**")

            for _, row in sb_df.iterrows():
                symptom = row["Gejala"]

                symptom_column, variant_column, frequency_column, edit_column, del_column = st.columns([4, 4, 4, 1, 1])
                symptom_column.text(symptom)
                variant_column.text(row["Variasi"] if row["Variasi"] else "-")
                frequency_column.text(row["Frekuensi"] if row["Frekuensi"] else "-")

                if edit_column.button("⚙️", key=f"{symptom}_edit", type="tertiary"):
                    edit_disease_symptom(chosen_disease, symptom, row["Variasi"], row["Frekuensi"], row["Id"])

                if del_column.button("🗑️", key=f"{symptom}_delete", type="tertiary"):
                    delete_disease_symptom(chosen_disease, symptom, row["Id"])

            if st.button("Tambah gejala penyakit"):
                add_disease_symptom(chosen_disease)
    
        else:
            st.text("Tidak ada data penyakit.")

    st.divider()

    if st.button("Keluar dari menu ubah data", type="tertiary"):
        del st.session_state["role"]
        st.rerun()
