Antiquities Service Archive — AI Translation & Exploration Platform
A Streamlit web application built to digitize, translate, and analyze early 20th-century administrative correspondence from the Egyptian Antiquities Service (Service des Antiquités de l'Égypte), covering the period from 1920 to 1950.

Overview
Unlike standard archival viewers, this platform is specifically engineered to handle the complex, bilingual reality of Egyptian administrative history. It processes official documents that feature typed French administrative text alongside handwritten Arabic marginalia, official routing stamps, and clerical annotations.

The core extraction engine utilizes Gemini 3.0 Pro to provide verbatim transcriptions, professional English translations, and structured metadata extraction, allowing researchers to trace historical threads involving key figures like Emile Baraize, P. Barsanti, and standard excavation labor and equipment logistics.

Core Features
Bilingual Transcription & Translation: Automatically processes mixed-language documents, outputting both the original French/Arabic text and a cohesive English translation.

Marginalia & Stamp Recognition: Explicitly tags and extracts handwritten Arabic routing notes, colored pencil marks, and official ink stamps (e.g., "Egyptian Government") into a searchable database schema.

Relational Filtering Matrix: Move beyond sequential viewing. Filter the archive by Date, Sender (e.g., P. Lacau, C.C. Edgar), Recipient, and specific administrative threads.

Side-by-Side Historical Viewer: A high-fidelity interface displaying the original, unedited archival scan alongside its parsed text, translation, and extracted metadata.

Structured Metadata Export: All processed documents are logged into a master metadata.csv for use in broader historical data analysis or external databases.

Repository Structure
Plaintext
antiquities-service-archive/
├── app.py                 # Main Streamlit interface and filtering matrix
├── transcribe_engine.py   # Core Gemini 3.0 Pro API logic and system prompt
├── requirements.txt       # Python dependencies
├── data/
│   ├── metadata.csv       # Master relational index of all processed documents
│   └── translations/      # JSON files containing individual pipeline outputs
└── assets/
    └── raw_scans/         # High-resolution, unedited source images
Running Locally
Clone the repository and navigate to the directory:

Bash
git clone <repository-url>
cd antiquities-service-archive
Install the required dependencies:

Bash
pip install -r requirements.txt
Set your API credentials as environment variables:

Bash
export OPENAI_API_KEY="your-gemini-api-key-here"
export OPENAI_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
export GEMINI_MODEL="gemini-3.0-pro"
Launch the application:

Bash
streamlit run app.py
Workflow
Drop Scans: Place high-resolution, unedited images of the archival records into the assets/raw_scans/ directory.

Process: The transcribe_engine.py reads the image, applies the strict historical system prompt, and generates a structured JSON output containing the transcriptions, translations, and metadata.

Explore: Open the Streamlit app to view the newly processed document, read the extracted Arabic marginalia, and filter by historical actors or date ranges.

AI Model Configuration
This application defaults to gemini-3.0-pro. The complexities of 1920s French bureaucratic phrasing, combined with the nuances of cursive handwritten Arabic marginalia, require the highest tier of reasoning and multilingual optical character recognition.
