import os  
import re  
import json  
import datetime  
from typing import Dict, Any, List  
  
import streamlit as st  
from pymongo import MongoClient  
import json
from preprocess import *  # Import your existing functions here
  
# -----------------------------  
# Configuration / MongoDB setup  
# -----------------------------  
def get_mongo_collection():  
    """  
    Returns a PyMongo collection handle to:  
      Database: certificstion_review_service  
      Collection: certification_review_service_tempcol  
    Reads the connection string from Streamlit secrets or the MONGODB_URI environment variable.  
    """  
    uri = "mongodb+srv://ashutoshbajpai:9xpWczP7G8VZemEk@cluster0.xvbny6o.mongodb.net/?appName=Cluster0"#st.secrets.get("MONGODB_URI") or os.environ.get("MONGODB_URI")  
    if not uri:  
        st.error("MongoDB URI not configured. Add MONGODB_URI to Streamlit secrets or environment variables.")  
        return None  
  
    try:  
        client = MongoClient(uri)  
        db = client["certificstion_review_service"]  # spelled per user request  
        collection = db["certification_review_service_tempcol"]  
        return collection  
    except Exception as e:  
        st.error(f"Failed to connect to MongoDB Atlas: {e}")  
        return None  
  
# -----------------------------  
# Utility functions  
# -----------------------------  
def sanitize_batch_name(batch_name: str) -> str:  
    """Sanitize batch name for safe file naming."""  
    batch_name = batch_name.strip()  
    return re.sub(r"[^A-Za-z0-9._-]+", "_", batch_name)  
  
def ensure_dir(path: str):  
    os.makedirs(path, exist_ok=True)  
  
def save_uploaded_files(files: List[st.runtime.uploaded_file_manager.UploadedFile], target_dir: str) -> List[str]:  
    """  
    Save uploaded files to target_dir with their original filenames.  
    """  
    saved_paths = []  
    for f in files:  
        original_name = f.name  
        save_path = os.path.join(target_dir, original_name)  
        with open(save_path, "wb") as out:  
            out.write(f.getbuffer())  
        saved_paths.append(save_path)  
    return saved_paths  
  
def generate_transformed_name(batch_name: str, index: int, original_filename: str) -> str:  
    """Create transformed filename like batchname_file{index}.ext"""  
    _, ext = os.path.splitext(original_filename)  
    return f"{batch_name}_file{index}{ext.lower()}"  
  
# -----------------------------  
# Placeholder analysis function  
# -----------------------------  
def analyze_file(file_path: str, original_name: str, transformed_name: str, batch_name: str) -> Dict[str, Any]:  
    """  
    Analyze each file and return a JSON structure.
    """

    response = analyze_inputdeck(file_path)  # Call the existing analysis function
    try:  
        json_dict = json.loads(response)  
        print(json_dict)  
    except json.JSONDecodeError as e:  
        print(f"Failed to parse JSON string: {e}")
    return json_dict
  
# -----------------------------  
# Batch processing  
# -----------------------------  
def process_and_store_batch(batch_name: str, uploaded_files: List[st.runtime.uploaded_file_manager.UploadedFile]) -> Dict[str, Any]:  
    """  
    - Saves files to a directory.  
    - Generates mapping of original -> transformed filenames.  
    - Renames saved files to transformed names.  
    - Calls placeholder analysis function for each file.  
    - Constructs final batch JSON object.  
    - Stores in MongoDB Atlas.  
    Returns the stored document or raises an exception.  
    """  
    collection = get_mongo_collection()  
    if collection is None:  
        raise RuntimeError("MongoDB collection not available.")  
  
    safe_batch = sanitize_batch_name(batch_name)  
    root_dir = os.path.abspath("uploads")  
    batch_dir = os.path.join(root_dir, safe_batch)  
    ensure_dir(batch_dir)  
  
    # Step 1: Save files with original names  
    saved_paths = save_uploaded_files(uploaded_files, batch_dir)  
  
    # Step 2 & 3: Create mapping and rename to transformed filenames  
    mapping: Dict[str, str] = {}  
    file_records: List[Dict[str, Any]] = []  
  
    for idx, original_path in enumerate(saved_paths, start=1):  
        original_name = os.path.basename(original_path)  
        transformed_name = generate_transformed_name(safe_batch, idx, original_name)  
        transformed_path = os.path.join(batch_dir, transformed_name)  
  
        # Rename the file on disk  
        os.replace(original_path, transformed_path)  
  
        # Step 4: Analyze each file  
        analysis_result = analyze_file(  
            file_path=transformed_path,  
            original_name=original_name,  
            transformed_name=transformed_name,  
            batch_name=safe_batch  
        )  
  
        # Collect mapping and record  
        mapping[original_name] = transformed_name  
        file_records.append({  
            "original_name": original_name,  
            "transformed_name": transformed_name,  
            "file_path": transformed_path,  
            "analysis": analysis_result  
        })  
  
    # Step 5: Construct final batch JSON  
    final_doc = {  
        "batch_name": batch_name,               # Original batch_name as entered by user  
        "batch_name_sanitized": safe_batch,     # Sanitized version used for filenames  
        "created_at": datetime.datetime.utcnow(),  
        "mapping": mapping,  
        "files": file_records  
    }  
  
    # Store in MongoDB Atlas  
    insert_result = collection.insert_one(final_doc)  
    final_doc["_id"] = str(insert_result.inserted_id)  
    return final_doc  
  
# -----------------------------  
# Dashboard rendering  
# -----------------------------  
def get_batches() -> List[str]:  
    collection = get_mongo_collection()  
    if collection is None:  
        return []  
    try:  
        batches = collection.distinct("batch_name")  
        return sorted([b for b in batches if isinstance(b, str)])  
    except Exception as e:  
        st.error(f"Error fetching batch list: {e}")  
        return []  
  
  
def get_latest_batch_doc(batch_name: str) -> Dict[str, Any]:  
    collection = get_mongo_collection()  
    if collection is None:  
        return {}  
    try:  
        doc = collection.find({"batch_name": batch_name}).sort([("created_at", -1)]).limit(1)  
        docs = list(doc)  
        if not docs:  
            return {}  
        d = docs[0]  
        if "_id" in d:  
            d["_id"] = str(d["_id"])  
        return d  
    except Exception as e:  
        st.error(f"Error fetching batch data: {e}")  
        return {}  
  
  
def render_file_dashboard(file_entry: Dict[str, Any]):  
    """  
    Renders a collapsible dashboard for a single file using its analysis JSON.  
    """

    original_name = file_entry.get("original_name", "Unknown file")  
    
    try:
        analysis = file_entry.get("analysis", {})
        # Extract sections  
        overview = analysis.get("overview", {})  
        details = analysis.get("details", {})  
        supplementary = analysis.get("supplementary", {})  
    
        # Overview content  
        recommendation = overview.get("recommendation", "N/A")  
        ai_score = overview.get("aiScore", "N/A")  
        hls = overview.get("highLevelSummary", {})  
    
        application_type = hls.get("applicationType", "N/A")  
        domain = hls.get("domain", "N/A")  
        current_db = hls.get("currentDatabase", "N/A")  
        is_ongoing_project = hls.get("isOngoingProject", "N/A")  
        high_level_summary = hls.get("summary", "N/A")  
    
        # Details content  
        missing_information = details.get("missingInformation", "No missing information.")  
    
        # Supplementary content  
        response_to_user = supplementary.get("responseToUser", "No response provided.")  
    except Exception as e:
        st.error(f"Error parsing analysis for file '{original_name}': {e}")
        return
    
    # ------------ Enhanced Presentation ------------ #  
    with st.expander(label=f"File: {original_name}", expanded=False):  
        # Recommendation and AI Score in Columns  
        col1, col2 = st.columns(2)  
        with col1:  
            st.metric(label="Recommendation", value=recommendation)  
        with col2:  
            st.metric(label="AI Score", value=ai_score)  
  
        # High-Level Summary Section  
        st.write("### High-Level Summary")  
        st.write(f"**Application Type:** {application_type}")  
        st.write(f"**Domain:** {domain}")  
        st.write(f"**Current Database:** {current_db}")  
        st.write(f"**Is Ongoing Project:** {is_ongoing_project}")  
        st.write("**Summary:**")  
        st.info(high_level_summary)  
  
        # Render Details Section  
        st.write("### Details")  
        if missing_information:  
            st.warning(missing_information)  
        else:  
            st.success("No missing information.")  
  
        # Render Supplementary Section  
        st.write("### Supplementary Information")  
        st.success(response_to_user)  
  
  
def render_dashboard():  
    """  
    Renders the main dashboard for certification review batches.  
    """  
    st.header("Certification Review: Dashboard")  
  
    # Fetch list of available batches  
    batches = get_batches()  
    if not batches:  
        st.info("No batches found. Upload and process a batch first.")  
        return  
  
    # Batch selection  
    selected_batch = st.selectbox("Select a Batch", batches)  
    if selected_batch:  
        # Fetch the latest batch document by batch name  
        batch_doc = get_latest_batch_doc(selected_batch)  
        files = batch_doc.get("files", [])  
        if not files:  
            st.warning("No files associated with this batch!")  
            return  
  
        # Display batch-level overview  
        st.write(f"### Batch: {batch_doc.get('batch_name')}")  
        st.write(f"**Created At:** {batch_doc.get('created_at')}")  
  
        st.write("---")  # Separator for clarity  
  
        # Render dashboard for each file  
        for file_entry in files:  
            render_file_dashboard(file_entry)
  
# -----------------------------  
# Upload & process UI  
# -----------------------------  
def render_upload_process():  
    st.header("Certification Review: Upload & Process")  
    batch_name = st.text_input("Batch name", help="Used to name files and group results into a batch.")  
    uploaded_files = st.file_uploader("Upload multiple files", accept_multiple_files=True)  
  
    if st.button("Process & Save"):  
        try:  
            result_doc = process_and_store_batch(batch_name, uploaded_files)  
            st.success(f"Batch '{batch_name}' processed and saved!")  
        except Exception as e:  
            st.error(f"Error processing batch: {e}")  
  
# -----------------------------  
# Main app  
# -----------------------------  
def main():  
    st.set_page_config(page_title="MongoDB SI Certification Review Platform", layout="wide")  
    st.title("MongoDB SI Certification Review Platform")  
  
    mode = st.sidebar.radio("Mode", ["Upload & Process", "Dashboard"])  
    if mode == "Upload & Process":  
        render_upload_process()  
    else:  
        render_dashboard()  
  
if __name__ == "__main__":  
    main()  
