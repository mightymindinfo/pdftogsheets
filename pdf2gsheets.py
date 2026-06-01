import os
import json
import time
import gspread
import streamlit as st
from pypdf import PdfReader
import google.generativeai as genai
from google.oauth2.service_account import Credentials

# ==========================================
# 1. BACKEND PROCESSING ENGINE FUNCTIONS
# ==========================================

def extract_text_from_pdf(pdf_file):
    """Opens an uploaded PDF file file-stream and extracts raw text."""
    try:
        reader = PdfReader(pdf_file)
        extracted_text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                extracted_text += f"\n--- PAGE {i+1} ---\n{page_text}"
        return extracted_text
    except Exception as e:
        raise Exception(f"Failed to read PDF file: {e}")


def analyze_and_map_with_gemma(raw_text, target_columns, api_key):
    """Passes raw text to Gemma-2.0-Flash to map into a clean JSON structure."""
    genai.configure(api_key=api_key)
    
    prompt = f"""
    You are an expert data migration agent. Analyze the unstructured document text below.
    Identify any tabular data and extract it.
    
    You MUST standardize the table headers. Force-map the extracted rows strictly into these keys:
    {target_columns}
    
    If the document uses different header words, use your intelligence to map them contextually to the requested keys.
    
    Return the result STRICTLY as a valid JSON array of objects. 
    Do not write any markdown code blocks, intro sentences, or conversational text. Return raw valid JSON text only.
    
    Unstructured Document Text:
    {raw_text}
    """
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    
    cleaned_json_text = response.text.strip()
    if cleaned_json_text.startswith("```json"):
        cleaned_json_text = cleaned_json_text.split("```json")[1].split("```")[0].strip()
    elif cleaned_json_text.startswith("```"):
        cleaned_json_text = cleaned_json_text.split("```")[1].split("```")[0].strip()
        
    return json.loads(cleaned_json_text)


def upload_batch_to_google_sheets(credentials_path, spreadsheet_id, target_columns, structured_data):
    """Authenticates securely and pushes data to a dynamic user-provided sheet."""
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    creds = Credentials.from_service_account_file(credentials_path, scopes=scopes)
    gc = gspread.authorize(creds)
    
    sh = gc.open_by_key(spreadsheet_id)
    worksheet = sh.get_worksheet(0)
    
    worksheet.clear()
    time.sleep(2) # Anti-quota breathe window
    
    master_batch = []
    master_batch.append(target_columns)  # Header row
    
    for row in structured_data:
        row_values = [row.get(col, "") for col in target_columns]
        master_batch.append(row_values)
        
    worksheet.append_rows(master_batch)

# ==========================================
# 2. STREAMLIT USER INTERFACE FRONTEND
# ==========================================

st.set_page_config(page_title="PDF Table Extractor", page_icon="📊", layout="wide")

st.title("🤖 AI Agentic Sheet Populator")
st.write("Upload any document containing a table, define your column schema, and watch the agent map and stream it into your personal Google Sheet live.")

# Sidebar for credentials and configuration
with st.sidebar:
    st.header("🔑 Connection Setup")
    
    # 1. Dynamic User Gemini Key
    user_api_key = st.text_input("Enter Gemini API Key:", type="password", help="Get this from Google AI Studio")
    
    st.write("---")
    st.subheader("📊 Google Sheets Destination")
    
    # 2. Dynamic User Spreadsheet ID
    user_spreadsheet_id = st.text_input("Enter Google Spreadsheet ID:", placeholder="e.g., 1A_BcDeFgHiJk...")
    
    # Check if the internal backend credentials file exists locally
    LOCAL_CREDS_PATH = 'credentials.json'
    if os.path.exists(LOCAL_CREDS_PATH):
        st.success("✅ Backend Service Credentials Loaded")
    else:
        st.error("❌ Missing 'credentials.json' file in your project folder!")

# Main window page layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📥 1. Upload Document")
    uploaded_file = st.file_uploader("Choose a PDF invoice or data sheet", type=["pdf"])
    
    st.subheader("📋 2. Define Target Columns")
    st.write("Enter the exact column names you want in your Google Sheet (comma-separated):")
    columns_input = st.text_input("Columns Layout:", value="Date, Vendor Name, Description, Total Amount")
    
    # Clean up the column entry string into a Python list
    target_columns_list = [col.strip() for col in columns_input.split(",") if col.strip()]

with col2:
    st.subheader("🚀 3. Run Pipeline")
    
    # Run button execution gate
    if st.button("Extract and Push Data", use_container_width=True):
        # Validation checks to guide the user
        if not user_api_key:
            st.error("Please enter your Gemini API Key in the sidebar!")
        elif not user_spreadsheet_id:
            st.error("Please enter a destination Google Spreadsheet ID!")
        elif not uploaded_file:
            st.error("Please upload a PDF file to extract first!")
        elif not os.path.exists(LOCAL_CREDS_PATH):
            st.error("Make sure your 'credentials.json' is saved into your project folder directory.")
        else:
            try:
                # Execution Flow
                with st.spinner("📄 Step 1: Reading document text..."):
                    extracted_text = extract_text_from_pdf(uploaded_file)
                    st.toast("Document text successfully parsed!")
                
                with st.spinner("🧠 Step 2: Handing data to Gemma for target header mapping..."):
                    parsed_json = analyze_and_map_with_gemma(extracted_text, target_columns_list, user_api_key)
                    st.toast(f"Gemma mapped {len(parsed_json)} data rows successfully!")
                    
                with st.spinner("📦 Step 3: Batch uploading rows into your Google Sheet..."):
                    upload_batch_to_google_sheets(LOCAL_CREDS_PATH, user_spreadsheet_id, target_columns_list, parsed_json)
                
                st.success("🎉 PIPELINE COMPLETE! Go check your open Google Sheet browser tab—the table has been updated!")
                st.balloons()
                
                # Show a little preview of what was sent
                st.write("### Data Extracted Preview:")
                st.json(parsed_json)
                
            except Exception as run_err:
                st.error(f"Execution Error occurred: {run_err}")