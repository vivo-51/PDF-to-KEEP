import streamlit as st
import google.generativeai as genai
import streamlit.components.v1 as components
import time
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="VIVO FILES", page_icon="📂", layout="centered")

# --- STYLE CSS ---
st.markdown("""
<style>
    .stApp { background-color: #f0f2f5; }
    .block-container { padding-top: 2rem; padding-bottom: 5rem; }
    
    .main-header { font-size: 2.5rem; font-weight: 900; color: #111; text-align: center; margin-bottom: 20px; }
    .vivo-text { color: #EAB308; font-weight: 300; }
    
    .counter-badge {
        background-color: #FEF08A; color: #854D0E;
        padding: 5px 15px; border-radius: 20px;
        font-weight: bold; font-size: 0.9rem;
        border: 1px solid #FDE047; margin-bottom: 10px; display: inline-block;
    }
    
    div.stButton > button {
        width: 100%; height: 70px; border-radius: 15px;
        font-size: 20px; font-weight: 900;
        background-color: #111827; color: white;
        border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    div.stButton > button:active { transform: scale(0.98); background-color: black; }
    div.stButton > button:hover { border-color: transparent; color: white; }
</style>
""", unsafe_allow_html=True)

# --- SETUP ---
if "notes" not in st.session_state: st.session_state.notes = []
if "export_mode" not in st.session_state: st.session_state.export_mode = False
if "current_note_index" not in st.session_state: st.session_state.current_note_index = 0

api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key: st.stop()
genai.configure(api_key=api_key)

def get_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if 'models/gemini-1.5-flash' in models: return 'models/gemini-1.5-flash'
        if 'models/gemini-1.5-pro' in models: return 'models/gemini-1.5-pro'
        return models[0] if models else None
    except: return None

def extract(file):
    model_name = get_model()
    if not model_name: return "Erreur: Modèle IA introuvable."
    try:
        model = genai.GenerativeModel(model_name)
        # On ne force plus le mime_type 'application/pdf' ici pour éviter les bugs Android
        # On laisse Gemini deviner ou on envoie les données brutes
        response = model.generate_content([
            {'mime_type': 'application/pdf', 'data': file.getvalue()},
            "Transcris tout le texte. Pas de résumé. Texte brut."
        ])
        return response.text
    except Exception as e: return f"Erreur lecture : {str(e)}"

# --- INTERFACE ---

if st.session_state.export_mode and len(st.session_state.notes) > 0:
    idx = st.session_state.current_note_index
    if idx >= len(st.session_state.notes):
        st.balloons()
        st.success("Toutes les notes sont exportées ! 🎉")
        if st.button("Recommencer"):
            st.session_state.export_mode = False
            st.session_state.current_note_index = 0
            st.rerun()
        st.stop()

    current_note = st.session_state.notes[idx]
    
    st.markdown(f'<div class="counter-badge">NOTE {idx + 1} / {len(st.session_state.notes)}</div>', unsafe_allow_html=True)
    st.markdown(f"### {current_note['title']}")
    st.text_area("Contenu", value=current_note['content'], height=250, disabled=True)

    safe_title = json.dumps(current_note['title'])
    safe_content = json.dumps(current_note['content'])
    
    components.html(f"""
    <html>
        <head>
            <style>
                button {{
                    background-color: #EAB308; color: #422006; border: none; width: 100%; height: 80px;
                    border-radius: 15px; font-family: sans-serif; font-weight: 900; font-size: 22px; cursor: pointer;
                    box-shadow: 0 4px 10px rgba(234, 179, 8, 0.4); display: flex; align-items: center; justify-content: center; gap: 10px;
                }}
                button:active {{ transform: scale(0.97); }}
            </style>
        </head>
        <body>
            <button onclick="share()">📤 ENVOYER VERS KEEP</button>
            <script>
                async function share() {{
                    const title = {safe_title};
                    const text = {safe_content};
                    try {{
                        if (navigator.share) {{ await navigator.share({{ title: title, text: text }}); }} 
                        else {{ await navigator.clipboard.writeText(text); window.open('https://keep.google.com/', '_blank'); }}
                    }} catch (e) {{}}
                }}
            </script>
        </body>
    </html>
    """, height=90)

    if st.button("✅ C'EST FAIT, SUIVANTE ➡️"):
        st.session_state.current_note_index += 1
        st.rerun()
        
    if st.button("❌ Arrêter", type="secondary"):
        st.session_state.export_mode = False
        st.rerun()

else:
    st.markdown('<div class="main-header">VIVO <span class="vivo-text">FILES</span></div>', unsafe_allow_html=True)
    st.caption("Importe tes PDF, extrais le texte, et clique sur LESSSSGO.")
    
    # "Open Bar" : On accepte tout, et on a retiré le filtre Python qui bloquait Android
    files = st.file_uploader("Tes fichiers PDF", accept_multiple_files=True)
    
    if files:
        if st.button("LESSSSGO", type="primary"):
            bar = st.progress(0, "Démarrage...")
            for i, f in enumerate(files):
                # PLUS AUCUNE VÉRIFICATION DE TYPE ICI
                # On envoie direct au charbon
                txt = extract(f)
                st.session_state.notes.append({"title": f.name, "content": txt})    
                bar.progress((i+1)/len(files), f"Fait : {f.name}")
            bar.empty()
            st.rerun()

    if len(st.session_state.notes) > 0:
        st.success(f"{len(st.session_state.notes)} notes prêtes !")
        if st.button("🚀 LANCER LA SÉQUENCE", type="primary"):
            st.session_state.export_mode = True
            st.session_state.current_note_index = 0
            st.rerun()
            
        with st.expander("Voir la liste"):
            for n in st.session_state.notes:
                st.write(f"- {n['title']}")
