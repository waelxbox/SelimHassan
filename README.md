# Antiquities Service Archive — AI Translation & Exploration Platform

A Streamlit web application built to digitize, translate, and analyze early 20th-century administrative correspondence from the Egyptian Antiquities Service (Service des Antiquités de l'Égypte), covering the period from 1920 to 1950.

## Overview

Unlike standard archival viewers, this platform is specifically engineered to handle the complex, bilingual reality of Egyptian administrative history. It processes official documents that feature typed French administrative text alongside handwritten Arabic marginalia, official routing stamps, and clerical annotations. 

The core extraction engine utilizes Gemini 3.0 Pro to provide verbatim transcriptions, professional English translations, and structured metadata extraction, allowing researchers to trace historical threads involving key figures like Emile Baraize, P. Barsanti, and standard excavation labor and equipment logistics.

## Core Features

* **Bilingual Transcription & Translation:** Automatically processes mixed-language documents, outputting both the original French/Arabic text and a cohesive English translation.
* **Marginalia & Stamp Recognition:** Explicitly tags and extracts handwritten Arabic routing notes, colored pencil marks, and official ink stamps (e.g., "Egyptian Government") into a searchable database schema.
* **Relational Filtering Matrix:** Move beyond sequential viewing. Filter the archive by Date, Sender (e.g., P. Lacau, C.C. Edgar), Recipient, and specific administrative threads.
* **Side-by-Side Historical Viewer:** A high-fidelity interface displaying the original, unedited archival scan alongside its parsed text, translation, and extracted metadata.
* **Structured Metadata Export:** All processed documents are logged into a master `metadata.csv` for use in broader historical data analysis or external databases.

## Repository Structure

```text
antiquities-service-archive/
├── app.py                 # Main Streamlit interface and filtering matrix
├── transcribe_engine.py   # Core API logic and system prompt
├── requirements.txt       # Python dependencies
├── data/
│   ├── metadata.csv       # Master relational index of all processed documents
│   └── translations/      # JSON files containing individual pipeline outputs
└── assets/
    └── raw_scans/         # High-resolution, unedited source images
