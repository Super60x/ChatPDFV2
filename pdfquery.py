import os
import logging
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.document_loaders import PyPDFium2Loader
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class PDFQuery:
    def __init__(self, openai_api_key = None) -> None:
        if not openai_api_key:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OpenAI API key must be provided or set in environment variables")
                
        os.environ["OPENAI_API_KEY"] = openai_api_key
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=openai_api_key,
            model="text-embedding-ada-002",
            chunk_size=1000
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=16000,
            chunk_overlap=3200,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        
        self.llm = ChatOpenAI(
            temperature=0,
            model="gpt-4",
            openai_api_key=openai_api_key,
            presence_penalty=-1.0,
            frequency_penalty=-1.0,
            max_tokens=4000
        )
        
        template = """Je bent een nauwkeurige assistent die alleen antwoord geeft op basis van de gegeven context.
        
        Belangrijke regels:
        1. Gebruik ALLEEN informatie die expliciet in de context staat
        2. Als je het antwoord niet kunt vinden in de context, zeg dat dan eerlijk
        3. Verzin NOOIT informatie die niet in de context staat
        4. Wees direct en to-the-point in je antwoorden
        5. Als er tabellen of lijsten in de context staan, geef deze correct weer
        6. Antwoord altijd in het Nederlands
        7. Als er meerdere relevante stukken informatie zijn, combineer deze in je antwoord
        8. Geef aan als je informatie uit verschillende delen van het document combineert
        9. Als je een deel van de tekst letterlijk citeert, gebruik dan aanhalingstekens
        
        Context: {context}
        
        Vraag: {question}
        
        Antwoord: Let op bovenstaande regels en geef een nauwkeurig antwoord."""
        
        PROMPT = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        self.chain = LLMChain(
            llm=self.llm,
            prompt=PROMPT,
            verbose=True
        )
        
        self.db = None
        self.persist_directory = "chroma_db"

    def ask(self, question: str) -> str:
        try:
            if not self.db or not self.chain:
                logging.warning("No document has been ingested yet")
                return "Upload eerst een document."

            try:
                # Get relevant documents
                docs = self.db.get_relevant_documents(question)
                if not docs:
                    logging.warning("No relevant documents found for the question")
                    return "Geen relevante informatie gevonden in het document."

                # Combine all document content
                context = "\n\n".join([doc.page_content for doc in docs])
                logging.info(f"Retrieved {len(docs)} relevant document chunks")

                # Generate response
                response = self.chain.run(context=context, question=question)
                return response.strip()

            except Exception as e:
                logging.error(f"Error during question processing: {str(e)}", exc_info=True)
                if "OpenAI API" in str(e):
                    raise ValueError("OpenAI API error occurred")
                raise

        except Exception as e:
            logging.error(f"Error in ask method: {str(e)}", exc_info=True)
            raise

    def ingest(self, file_path: os.PathLike) -> None:
        try:
            logging.info(f"Starting ingestion for file: {file_path}")
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
                
            if not os.path.getsize(file_path):
                raise ValueError("File is empty")
            
            # Clear previous database if it exists
            if os.path.exists(self.persist_directory):
                try:
                    import shutil
                    shutil.rmtree(self.persist_directory)
                    logging.info("Cleared previous vector store")
                except Exception as e:
                    logging.error(f"Error clearing previous vector store: {str(e)}")
                
            try:
                loader = PyPDFium2Loader(file_path)
                documents = loader.load()
            except Exception as e:
                logging.error(f"Error loading PDF: {str(e)}")
                raise ValueError(f"Could not read PDF file: {str(e)}")
            
            if not documents:
                raise ValueError("No content could be extracted from the PDF")
                
            logging.info(f"Loaded {len(documents)} pages from file: {file_path}")
            
            try:
                splitted_documents = self.text_splitter.split_documents(documents)
                logging.info(f"Split documents into {len(splitted_documents)} chunks")
                
                if not splitted_documents:
                    raise ValueError("Document splitting resulted in no chunks")
                
                # Create vector store
                vectorstore = Chroma.from_documents(
                    documents=splitted_documents,
                    embedding=self.embeddings,
                    persist_directory=self.persist_directory
                )
                
                # Create retriever with search parameters
                self.db = vectorstore.as_retriever(
                    search_kwargs={
                        "k": 100,
                    }
                )
                
                logging.info("Vector store initialized successfully")
                
            except Exception as e:
                logging.error(f"Error processing document chunks: {str(e)}")
                raise ValueError(f"Error processing document content: {str(e)}")
            
        except Exception as e:
            logging.error(f"Error during document ingestion: {str(e)}")
            raise

    def forget(self):
        """Reset the database and chain"""
        self.db = None
        if os.path.exists(self.persist_directory):
            import shutil
            shutil.rmtree(self.persist_directory)
            logging.info("Cleared previous vector store")