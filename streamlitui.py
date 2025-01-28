import os
import tempfile
import streamlit as st
import streamlit.components.v1 as components
import requests
import logging

# Set page configuration at the start
st.set_page_config(page_title="PDF Chat", layout="wide")

from streamlit_chat import message
from pdfquery import PDFQuery
from dotenv import load_dotenv
from PyPDF2 import PdfReader

# Load environment variables
load_dotenv(override=True)

# Configure logging with a rotating file handler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.handlers.RotatingFileHandler(
            "streamlit_debug.log",
            maxBytes=1024*1024,  # 1MB
            backupCount=5,
            mode='a'
        ),
        logging.StreamHandler()
    ]
)

# Add a startup log message
logging.info("Streamlit application started")
logging.getLogger().handlers[0].flush()

# Add custom CSS for styling
st.markdown(
    """
    <style>
    /* Input field styling */
    .stTextInput > div > div > input {
        background-color: #f0f2f6;
        border: 1px solid #e0e3e9;
        padding: 12px;
        border-radius: 8px;
        height: 45px;
        font-size: 16px;
    }

    /* Chat container styling */
    .chat-container {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

    /* Summary button styling */
    .stButton > button:first-child {
        background-color: #4caf50;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 16px;
        font-weight: 600;
        border: none;
        margin: 10px 0;
        transition: all 0.3s;
    }
    .stButton > button:first-child:hover {
        background-color: #388e3c;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }

    /* File uploader styling */
    .stFileUploader {
        padding: 20px;
        border-radius: 10px;
        background-color: #f9f9f9;
        border: 2px dashed #bbb;
        margin-bottom: 20px;
    }

    /* Chat message styling */
    .message {
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        max-width: 80%;
    }
    .message.user {
        background-color: #e3f2fd;
        margin-left: auto;
    }
    .message.bot {
        background-color: #f5f5f5;
        margin-right: auto;
    }
    
    /* Divider styling */
    hr {
        margin: 20px 0;
        border: none;
        border-top: 1px solid #e0e0e0;
    }

    /* Chat form styling */
    .chat-form {
        display: flex;
        align-items: flex-start;
        gap: 10px;
    }

    /* Column spacing */
    .stColumns {
        gap: 20px;
    }
    
    .stButton > button {
        cursor: pointer;
    }
    
    .stTextInput > div > div > input {
        cursor: pointer;
    }
    
    .copy-text-container {
        margin-top: 10px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def display_messages():
    # st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    # st.subheader("Chat")
    # for i, (msg, is_user) in enumerate(st.session_state["messages"]):
    #     alignment = 'flex-start' if is_user else 'flex-end'
    #     margin = 'margin-right' if is_user else 'margin-left'
    #     st.markdown(
    #         f"""
    #         <div class="{'user' if is_user else 'bot'}-message-container" style="display: flex; justify-content: {alignment}; margin: 1rem;">
    #             <div style="background: {'#E3F2FD' if is_user else '#F5F5F5'}; padding: 1rem; border-radius: 0.5rem; {margin}: 0.5rem; max-width: 70%;">
    #                 <div style="font-weight: bold; margin-bottom: 0.5rem;">{'👤' if is_user else '🤖'}</div>
    #                 <div>{msg}</div>
    #             </div>
    #         </div>
    #         """,
    #         unsafe_allow_html=True
    #     )
    # st.markdown('</div>', unsafe_allow_html=True)
    st.session_state["thinking_spinner"] = st.empty()

def process_input():
    if st.session_state["user_input"] and len(st.session_state["user_input"].strip()) > 0:
        user_text = st.session_state["user_input"].strip()
        
        if not st.session_state.get("pdfquery") or not st.session_state["pdfquery"].db:
            st.error("Upload eerst een document.")
            return
            
        try:
            with st.session_state["thinking_spinner"], st.spinner(f"Bezig met denken..."):
                answer = st.session_state["pdfquery"].ask(user_text)
                if answer:
                    st.session_state["messages"].append((user_text, True))
                    st.session_state["messages"].append((answer, False))
                    st.session_state["user_input"] = ""
                
        except Exception as e:
            logging.error(f"Error in chat: {str(e)}", exc_info=True)
            error_msg = str(e)
            if "OpenAI API" in error_msg:
                st.error("Er is een probleem met de OpenAI API verbinding. Controleer je API sleutel.")
            elif "No relevant" in error_msg:
                st.warning("Geen relevante informatie gevonden. Probeer je vraag anders te formuleren.")
            else:
                st.error("Er is een fout opgetreden bij het verwerken van je vraag. Probeer het opnieuw.")

def process_uploaded_file(file):
    try:
        logging.info(f"Processing file: {file.name}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tf:
            try:
                tf.write(file.getbuffer())
                tf.flush()
                file_path = tf.name
                logging.info(f"Created temporary file: {file_path}")

                with st.session_state["ingestion_spinner"], st.spinner(f"Bezig met verwerken van {file.name}"):
                    if os.path.getsize(file_path) == 0:
                        raise ValueError("Uploaded file is empty")
                        
                    st.session_state["pdfquery"].ingest(file_path)
                    logging.info(f"Successfully ingested file: {file.name}")
                    st.session_state["document_processed"] = True
                    
            except Exception as e:
                logging.error(f"Error processing file {file.name}: {str(e)}")
                st.session_state["document_processed"] = False
                raise
                
            finally:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logging.info(f"Removed temporary file: {file_path}")
                except Exception as e:
                    logging.error(f"Error removing temporary file {file_path}: {str(e)}")
                    
    except Exception as e:
        logging.error(f"Error in process_uploaded_file: {str(e)}")
        error_msg = str(e)
        if "OpenAI API" in error_msg:
            st.error("Er is een probleem met de OpenAI API verbinding. Controleer je API sleutel.")
        elif "empty" in error_msg.lower():
            st.error("Het geüploade bestand is leeg. Upload een geldig PDF bestand.")
        else:
            st.error("Er is een fout opgetreden bij het verwerken van het bestand. Probeer het opnieuw.")

def extract_text_from_uploaded_pdf():
    if st.session_state["pdf_uploader"]:
        file = st.session_state["pdf_uploader"][0]
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(file.getbuffer())
            file_path = tf.name

        reader = PdfReader(file_path)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
        os.remove(file_path)
        return text
    else:
        return ''

def generate_summary_with_chatgpt(document_text):
    # Use ChatGPT to generate a real summary of the document
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        messages=[
            {"role": "user", "content": f"Samenvatting van het volgende aanbestedingsdocument voor de Nederlandse mobiliteitsmarkt: {document_text}. \n\n- Altijd in het Nederlands antwoorden\n- Creëer een duidelijke structuur\n- Focus op vereisten die nodig zijn om de aanbesteding te winnen\n- Focus op deadlines die gehaald moeten worden\n- Focus op specifieke belangrijke punten die de aanbesteding zullen winnen"}
        ],
        model="gpt-4o",
        max_tokens=5000  # Adjust token limit if needed
    )
    summary = response.choices[0].message.content.strip()
    return summary

def make_summary():
    with st.spinner("Samenvatting genereren..."):
        document_text = extract_text_from_uploaded_pdf()
        summary = generate_summary_with_chatgpt(document_text)
        st.session_state["summary"] = summary

def search_with_perplexity(query):
    api_key = os.getenv("PERPLEXITY_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(f"https://api.perplexity.ai/search?q={query}", headers=headers)

    if response.status_code == 200:
        data = response.json()
        return {"answer": data.get("answer", "No answer found")}
    else:
        logging.error(f"Error retrieving data: {response.status_code} - {response.text}")
        return {"answer": "Error retrieving data"}

def main():
    # Initialize session state variables
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "OPENAI_API_KEY" not in st.session_state:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            st.session_state.OPENAI_API_KEY = api_key
        else:
            st.error("OpenAI API sleutel niet gevonden in .env bestand")
            st.session_state.OPENAI_API_KEY = ""
    if "pdfquery" not in st.session_state:
        if st.session_state.OPENAI_API_KEY:
            st.session_state.pdfquery = PDFQuery(st.session_state.OPENAI_API_KEY)
        else:
            st.session_state.pdfquery = None
    if "ingestion_spinner" not in st.session_state:
        st.session_state.ingestion_spinner = st.empty()
    if "thinking_spinner" not in st.session_state:
        st.session_state.thinking_spinner = st.empty()

    st.header("PDF Chat")

    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Document uploaden")
        st.markdown('<div class="file-upload-container">', unsafe_allow_html=True)
        
        if not st.session_state.OPENAI_API_KEY:
            st.error("Voeg eerst een OpenAI API sleutel toe in het .env bestand")
            return
            
        uploaded_files = st.file_uploader(
            "Upload PDF bestanden",
            type=["pdf"],
            accept_multiple_files=True,
            key="pdf_uploader"
        )
        
        if uploaded_files:
            for file in uploaded_files:
                process_uploaded_file(file)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.button("📄 Maak Samenvatting", on_click=make_summary, use_container_width=True)

    with col2:
        st.subheader("Samenvatting")
        if "summary" in st.session_state:
            summary_text = st.session_state["summary"]
            st.markdown(summary_text)

if __name__ == "__main__":
    main()