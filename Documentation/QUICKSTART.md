# Quick Start Guide

## Prerequisites
1. Python installed on your system
2. OpenAI API key

## Setup

1. **Environment Setup**
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   .\venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configure API Key**
   - Create a `.env` file in the root directory
   - Add your OpenAI API key:
     ```
     OPENAI_API_KEY=your-api-key-here
     ```

## Running the Application

1. **Start the Application**
   ```bash


   # Start the Streamlit server
   streamlit run streamlitui.py
   ```
   The application will automatically open in your default web browser. If it doesn't, you can access it at http://localhost:8501

2. **Using the App**
   - Upload your PDF document(s)
   - Wait for processing to complete
   - Start asking questions about your documents
   - The app will provide context-aware responses, including tables when relevant

## Notes
- The app will automatically load your API key from the `.env` file
- Multiple PDFs can be uploaded and processed
- Responses are formatted with bold text and preserve table structures
- All UI elements are in Dutch
