import streamlit as st
import google.generativeai as genai

# Configuration de la page
st.set_page_config(page_title="Extracteur PDF Viv", page_icon="📝", layout="centered")

# --- PARTIE 1 : CONFIGURATION SÉCURISÉE ---
# L'app va chercher la clé dans le coffre-fort de Streamlit (Secrets)
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    st.error("⚠️ Clé API introuvable. Avez-vous bien configuré les 'Secrets' dans Streamlit ?")
    st.stop()

def extract_content(uploaded_file):
    """Envoie le PDF à Gemini pour extraction brute"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Lecture du fichier
        bytes_data = uploaded_file.getvalue()
        
        # Instructions strictes pour l'IA
        prompt = """
        Tu es un transcripteur automatique.
        TA MISSION : Extraire tout le texte de ce PDF.
        RÈGLES :
        1. AUCUN résumé.
        2. AUCUN ajout (pas de 'Voici le texte', pas de bonjour).
        3. Copie intégrale mot pour mot.
        4. Si le texte est long, ne t'arrête pas avant la fin.
        """
        
        response = model.generate_content([
            {'mime_type': 'application/pdf', 'data': bytes_data},
            prompt
        ])
        return response.text
    except Exception as e:
        return f"Erreur de lecture : {str(e)}"

# --- PARTIE 2 : INTERFACE ---

st.title("📝 Extracteur PDF pour Keep")
st.info("Cette app traite tout en local via l'API. Rien n'est stocké.")

# Zone pour déposer les fichiers
uploaded_files = st.file_uploader("Déposez vos PDF ici (1 ou 100, peu importe)", 
                                  type=['pdf'], 
                                  accept_multiple_files=True)

if uploaded_files:
    st.write("---")
    st.success(f"🚀 {len(uploaded_files)} fichiers reçus. Démarrage de l'extraction...")
    
    # Barre de progression
    my_bar = st.progress(0)
    
    for i, file in enumerate(uploaded_files):
        # On crée un bloc pliable pour chaque fichier
        with st.expander(f"✅ Terminé : {file.name}", expanded=True):
            with st.spinner(f"Lecture de {file.name}..."):
                text_result = extract_content(file)
                
                # Zone de texte facile à copier
                st.text_area("Texte extrait (Cliquez dans la case, Ctrl+A, Ctrl+C)", 
                             value=text_result, 
                             height=200,
                             key=f"text_{i}")
                
        # Avance la barre
        my_bar.progress((i + 1) / len(uploaded_files))

    st.balloons()
    st.success("Tâche terminée ! Vous pouvez copier les textes ci-dessus.")
