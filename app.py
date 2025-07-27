import streamlit as st
import ollama
import json
import os

# --- System Prompt ---
SYSTEM_PROMPT = (
    "You are an assistant providing Islamic reflections (Tadabbur) on the Qur'an. "
    "Only use the ayah and classical tafsir text provided. Do not offer personal or theological interpretations. "
    #"Use the ayah provided, offer personal and theological interpretations. "
    "Focus on drawing personal moral, ethical, and spiritual lessons from the classical tafsir."
)

# --- Load Quran Data ---
def load_quran_data():
    if os.path.exists("quran.json"):
        with open("quran.json", "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        st.error("Missing quran.json file.")
        return {}

# --- Load Tafsir for Surah ---
def load_tafsir(author_folder, surah_number):
    tafsir_path = os.path.join("data", author_folder, f"{surah_number}.json")
    if os.path.exists(tafsir_path):
        with open(tafsir_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return []

quran_data = load_quran_data()

# --- App UI ---
st.set_page_config(page_title="Qur'an Reflection Generator", layout="wide")
st.title("📖 Qur'an Reflection Generator")

author_folder = st.selectbox("Select Tafsir Author", [
    "ibn-katheer",
    "tabari",
    "qurtubi",
    "alrazi",
    "alaloosi",
    "ibn-aashoor"
])

surah_numbers = sorted([int(k) for k in quran_data.keys()])
surah_number = st.selectbox("Select Surah Number", surah_numbers)
surah_data = quran_data.get(str(surah_number), {})
ayah_numbers = sorted([int(k) for k in surah_data.keys()])
ayah_number = st.selectbox("Select Ayah Number", ayah_numbers)

ayah_text_ar = surah_data.get(str(ayah_number), {}).get("arabic", "")
st.text_area("Arabic Ayah", value=ayah_text_ar, height=100, disabled=True)

# --- Load tafsir text for this ayah ---
tafsir_entries = load_tafsir(author_folder, surah_number)
tafsir_text = ""
for entry in tafsir_entries:
    start, end = entry["ayah_range"]
    if start <= ayah_number <= end:
        tafsir_text = entry["tafsir_text"]
        break

st.text_area("Tafsir Excerpt", value=tafsir_text, height=200, disabled=True)

model = st.selectbox("Choose Ollama Model", [
    "nous-hermes2",
    "openhermes-2.5-mistral",
    "phi3:mini",
    "gemma:7b"
])

if st.button("Generate Reflection"):
    if not tafsir_text.strip():
        st.warning("No tafsir text available for this ayah.")
    else:
        prompt = (
            f"Arabic Ayah:\n{ayah_text_ar}\n\n"
            f"Tafsir Commentary:\n{tafsir_text}\n\n"
            f"Based on the above, generate a brief, insightful reflection focusing on spiritual or moral lessons."
        )

        full_prompt = f"<|system|>\n{SYSTEM_PROMPT}\n<|user|>\n{prompt}\n<|assistant|>"

        try:
            response = ollama.generate(
                model=model,
                prompt=full_prompt,
                options={'temperature': 0.7},
                keep_alive=-1
            )
            result_text = response
            
            if response.done:
                result_text = response['response']
                st.success("Reflection Generated:")
                st.markdown(f"> {result_text}")

                # Save reflection to file
                author_path = os.path.join("reflections", author_folder)
                os.makedirs(author_path, exist_ok=True)
                save_path = os.path.join(author_folder, str(surah_number))
                os.makedirs(save_path, exist_ok=True)
                file_name = f"{ayah_number}.txt"
                with open(os.path.join(save_path, file_name), "w", encoding="utf-8") as f:
                    f.write(result_text)

                if st.download_button("Download Reflection", response['response_text'], file_name=f"reflection_{author_folder}_{surah_number}_{ayah_number}.txt"):
                    st.toast("File saved successfully.", icon="📁")
                else:
                    st.error("Model Error: ")

        except Exception:
            st.error("The model took too long to respond. Try a smaller model or simpler prompt.")
