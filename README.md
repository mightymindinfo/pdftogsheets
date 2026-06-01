# PDF to Google Sheets Agentic Sheet Populator

An intelligent, agent-driven data migration pipeline that extracts unstructured tabular data from PDF files and streams it into a structured Google Sheet. Built completely in Python using **Streamlit**, **Gemma 2.0 Flash**, and the **Google Sheets API**.

---

## 🚀 Features

* **Dynamic File Parsing:** Extracts raw document text layout structures from uploaded physical PDFs using `pypdf`.
* **Agentic Header Mapping:** Leverages **Gemma 2.0 Flash** to read messy, unstructured document text and intelligently force-map variable headers into exact user-defined key categories.
* **Network-Optimized Uploads:** Validates data structures into a unified matrix array before performing a single, high-performance batch-upload call via `gspread` to stay safely within Google API quota thresholds.
* **Fully Dynamic UI:** Allows users to input their own Gemini API keys, target Spreadsheet IDs, and custom column criteria seamlessly through an intuitive frontend.

---

## 🛠️ Architecture Workflow

1. **User Input:** User uploads a PDF (e.g., invoice, receipt, financial report) and inputs a comma-separated list of target columns.
2. **Data Extraction:** Python background extraction reads the document text structures page by page.
3. **AI Transformation:** Gemma interprets the layout, filters out conversational noise, maps matching contexts to requested keys, and formats the output into strict JSON arrays.
4. **Cloud Execution:** The app securely validates the credentials, wipes out past placeholder records, and pushes the new formatted dataset to Google Sheets instantly.

---

## 📋 Prerequisites & Setup

### 1. Google Cloud Service Account Credentials
To let the app write directly to your Google Sheet workspace:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and enable the **Google Sheets API** and **Google Drive API**.
3. Create a **Service Account**, generate a **JSON Key**, and download it.
4. Rename the downloaded file to exactly `credentials.json` and place it directly inside your local root project directory.
5. Open your target Google Sheet in your browser and share write access with the `client_email` address found inside your `credentials.json`.

### 2. Environment Installation
Clone the repository locally, navigate to your project directory, and install the required library stacks:

```bash
pip install streamlit gspread google-auth pypdf google-generativeai
