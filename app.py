import streamlit as st
import google.generativeai as genai
import time

# --- CONFIG ---
st.set_page_config(page_title="PDF to Keep TURBO", page_icon="⚡", layout="wide")

# --- STYLE ---
st.markdown("""
<style>
    .stApp { background-color: #F1F3F4; }
    .main-header { font-size: 2rem; font-weight: 900; color: #111; }
    .turbo-text { color: #EAB308; font-weight: 300; }
    .stButton>button { border-radius: 12px; font-weight: bold; border: none; }
    .stButton>button:hover { transform: scale(1.02); }
</style>
""", unsafe_allow_html=True)

# --- SETUP ET AUTO-DÉTECTION ---
if "notes" not in st.session_state: st.session_state.notes = []
if "export_mode" not in st.session_state: st.session_state.export_mode = False
if "current_note_index" not in st.session_state: st.session_state.current_note_index = 0

# Récupération de la clé
api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("⚠️ Clé API manquante dans les Secrets.")
    st.stop()

genai.configure(api_key=api_key)

# FONCTION INTELLIGENTE QUI TROUVE LE BON MODÈLE
def get_working_model():
    """Demande à Google quel modèle est disponible et prend le meilleur."""
    try:
        # On liste les modèles disponibles pour ta clé
        available = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available.append(m.name)
        
        # On cherche Flash en priorité, sinon Pro, sinon le premier qui vient
        if 'models/gemini-1.5-flash' in available:
            return 'models/gemini-1.5-flash'
        elif 'models/gemini-1.5-pro' in available:
            return 'models/gemini-1.5-pro'
        elif available:
            return available[0] # On prend le premier qui existe
        else:
            return None
    except Exception as e:
        return None

# --- MOTEUR D'EXTRACTION ---
def extract_content(uploaded_file):
    model_name = get_working_model()
    
    if not model_name:
        return "ERREUR CRITIQUE : Aucun modèle IA n'a été trouvé pour cette clé API. Vérifiez votre clé."

    try:
        model = genai.GenerativeModel(model_name)
        bytes_data = uploaded_file.getvalue()
        prompt = "Transcris l'intégralité du texte de ce PDF. Aucun résumé. Texte brut uniquement."
        
        response = model.generate_content([{'mime_type': 'application/pdf', 'data': bytes_data}, prompt])
        return response.text
    except Exception as e:
        return f"Erreur technique ({model_name}) : {str(e)}"

# --- INTERFACE ---
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<div class="main-header">PDF to Keep <span class="turbo-text">TURBO</span></div>', unsafe_allow_html=True)

# Mode Export
if st.session_state.export_mode and len(st.session_state.notes) > 0:
    idx = st.session_state.current_note_index
    current_note = st.session_state.notes[idx]
    
    st.info(f"⚡ NOTE {idx + 1} / {len(st.session_state.notes)}")
    st.markdown(f"### 📄 {current_note['title']}")
    st.code(current_note['content'], language="text")
    
    c1, c2 = st.columns([1, 1])
    with c1: st.link_button("🚀 OUVRIR KEEP", "https://keep.google.com/", use_container_width=True)
    with c2:
        if idx < len(st.session_state.notes) - 1:
            if st.button("Suivant ➡️", type="primary", use_container_width=True):
                st.session_state.current_note_index += 1
                st.rerun()
        else:
            if st.button("✅ Terminer", type="primary", use_container_width=True):
                st.session_state.export_mode = False
                st.rerun()

# Mode Import
else:
    with st.expander("📂 IMPORTER", expanded=True):
        uploaded_files = st.file_uploader("Glissez vos PDF", type=['pdf'], accept_multiple_files=True)
        if uploaded_files and st.button(f"GO ({len(uploaded_files)})", type="primary"):
            my_bar = st.progress(0, text="Démarrage...")
            for i, file in enumerate(uploaded_files):
                text = extract_content(file)
                st.session_state.notes.insert(0, {"id": str(time.time()), "title": file.name, "content": text})
                my_bar.progress((i + 1) / len(uploaded_files), text=f"Fait : {file.name}")
            my_bar.empty()
            st.rerun()

    if len(st.session_state.notes) > 0:
        st.markdown("---")
        if st.button("⚡ LANCER L'EXPORT", type="primary"):
            st.session_state.export_mode = True
            st.session_state.current_note_index = 0
            st.rerun()
        
        for note in st.session_state.notes:
            st.text_area(note['title'], value=note['content'], height=100, disabled=True)
