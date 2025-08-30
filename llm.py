import streamlit as st
from openai import OpenAI

client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"],
)

def generate_description(context):
    response = client.responses.create(
        model="gpt-4o-mini",
        instructions="Kamu adalah asisten yang memberikan penjelasan terkait suatu terminologi dalam tanya-jawab dokter-pasien untuk mengidentifikasi penyakit. Penjelasan yang diberikan harus sesederhana mungkin sehingga dapat dipahami oleh orang awam. Penjelasan hanya dapat terdiri maksimal dua kalimat. Penjelasan yang diberikan berformat teks biasa, bukan markdown. Kamu hanya merespons hal yang berkaitan dengan identifikasi penyakit, bukan hal lain.",
        input=f"Buatlah penjelasan singkat tentang \"{context}\". Jika tidak relevan, jawablah \"???\".",
    )
    return response.output_text
