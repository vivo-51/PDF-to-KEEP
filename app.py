import streamlit as st
import google.generativeai as genai
import time

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="PDF to Keep TURBO", page_icon="⚡", layout="wide")

# --- STYLE CSS ---
st.markdown("""
<style>
    .stApp { background-color: #F1F3F4; }
    .main-header { font-size: 2rem; font-weight: 900; color: #111; }
    .turbo-text { color: #EAB308; font-weight: 300; }
    .stButton>button { border-radius: 12px; font-weight: bold; border: none; }
    .stButton>button:hover { transform: scale(1.02); }
    .note-card { background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- GESTION DE LA CLÉ API ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("⚠️ Clé API introuvable dans les Secrets.")
        st.stop()
except Exception:
    st.error("⚠️ Erreur de configuration Secrets.")
    st.stop()

# --- INITIALISATION SESSION ---
if "notes" not in st.session_state:
    st.session_state.notes = []
if "export_mode" not in st.session_state:
    st.session_state.export_mode = False
if "current_note_index" not in st.session_state:
    st.session_state.current_note_index = 0

# --- FONCTION D'EXTRACTION (ROBUSTE) ---
def extract_content(uploaded_file):
    bytes_data = uploaded_file.getvalue()
    prompt = "Transcris l'intégralité du texte de ce PDF. Aucun résumé. Texte brut uniquement."
    
    # Liste des modèles à essayer dans l'ordre (Si Flash échoue, on tente Pro)
    models_to_try = ['gemini-1.5-flash-latest', 'gemini-1.5-flash', 'gemini-1.5-pro-latest']
    
    last_error = ""
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content([{'mime_type': 'application/pdf', 'data': bytes_data}, prompt])
            return response.text
        except Exception as e:
            last_error = str(e)
            continue # On essaie le suivant
            
    return f"Erreur fatale sur tous les modèles : {last_error}"

# --- HEADER ---
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<div class="main-header">PDF to Keep <span class="turbo-text">TURBO</span></div>', unsafe_allow_html=True)

# --- MODE EXPORTATION ---
if st.session_state.export_mode and len(st.session_state.notes) > 0:
    idx = st.session_state.current_note_index
    current_note = st.session_state.notes[idx]
    
    st.markdown("---")
    st.info(f"⚡ MODE TURBO : Note {idx + 1} sur {len(st.session_state.notes)}")
    
    st.markdown(f"### 📄 {current_note['title']}")
    st.code(current_note['content'], language="text")
    st.caption("👆 Cliquez sur le bouton 'Copier' en haut à droite du bloc gris.")

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.link_button("🚀 OUVRIR GOOGLE KEEP", "https://keep.google.com/", use_container_width=True)
    
    c_prev, c_next = st.columns(2)
    with c_prev:
        if idx > 0:
            if st.button("⬅️ Précédent"):
                st.session_state.current_note_index -= 1
                st.rerun()
    with c_next:
        if idx < len(st.session_state.notes) - 1:
            if st.button("Suivant ➡️", type="primary"):
                st.session_state.current_note_index += 1
                st.rerun()
        else:
            if st.button("✅ Terminer"):
                st.session_state.export_mode = False
                st.rerun()

# --- MODE DASHBOARD ---
else:
    with st.expander("📂 IMPORTER DES DOCUMENTS", expanded=True):
        uploaded_files = st.file_uploader("Glissez vos PDF ici", type=['pdf'], accept_multiple_files=True)
        
        if uploaded_files:
            if st.button(f"LANCER L'EXTRACTION ({len(uploaded_files)})", type="primary"):
                progress_text = "Opération Turbo en cours..."
                my_bar = st.progress(0, text=progress_text)
                
                for i, file in enumerate(uploaded_files):
                    text = extract_content(file)
                    new_note = {
                        "id": str(time.time()),
                        "title": file.name.replace('.pdf', ''),
                        "content": text
                    }
                    st.session_state.notes.insert(0, new_note)
                    my_bar.progress((i + 1) / len(uploaded_files), text=f"Extraction de {file.name}...")
                
                my_bar.empty()
                st.success("Extraction terminée !")
                st.rerun()

    if len(st.session_state.notes) > 0:
        st.markdown("---")
        c1, c2 = st.columns([3, 1])
        with c1: st.subheader(f"📑 Mes Notes ({len(st.session_state.notes)})")
        with c2: 
            if st.button("⚡ LANCER L'EXPORT", type="primary"):
                st.session_state.export_mode = True
                st.session_state.current_note_index = 0
                st.rerun()
        
        for note in st.session_state.notes:
            with st.container():
                st.markdown(f"**{note['title']}**")
                st.text_area("Aperçu", value=note['content'], height=100, key=note['id'], disabled=True)
                st.markdown("---")
