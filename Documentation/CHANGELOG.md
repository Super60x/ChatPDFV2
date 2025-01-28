# PDF Chat Tool - Changelog

## Latest Updates

### UI and Language
- Translated entire application interface to Dutch
- Improved response formatting with bold text and structured paragraphs
- Removed OpenAI API key input from frontend for security

### Data Handling
- Implemented persistent ChromaDB for better data storage
- Increased chunk size to 2000 and overlap to 400 for better context handling
- Added custom text separators for improved table detection

### Table and Content Processing
- Enhanced table detection and preservation in responses
- Added specific handling for planning-related queries
- Improved paragraph handling to maintain table structure
- Added Dutch keywords for planning detection

### Environment and Configuration
- Moved OpenAI API key to `.env` file
- Added proper environment variable loading
- Implemented better error handling for missing API keys

## Core Features
- PDF document upload and processing
- Interactive chat interface
- Support for multiple PDF uploads
- Intelligent text chunking and embedding
- Context-aware responses
- Table and structured content preservation
