import pandas as pd
from pypdf import PdfReader
import docx
import streamlit as st

from openai import OpenAI
from dotenv import load_dotenv
import os


st.set_page_config(
    page_title="Lab Folks AI",
    page_icon="🧪",
    layout="wide"
)
# Load API key
load_dotenv()

client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"]
)

# App title
st.markdown("""
# 🧪 Lab Folks AI Assistant
### AI-powered lab report analysis for biochemistry, PCR, HPLC, ELISA, LC-MS, and more.
""")

st.info("Upload lab files, enter your experiment details, and let Lab Folks AI help interpret your results.")
st.caption("AI-Powered Biochemistry & Laboratory Analysis Tool")

# ---------------- USER INPUTS ---------------- #

st.subheader("Lab Information")

lab_type = st.selectbox(
    "Choose Lab Type",
    [
        "PCR / Gel Electrophoresis",
        "HPLC",
        "ELISA",
        "LC-MS",
        "GC-MS",
        "Western Blot",
        "Spectrophotometry",
        "Other"
    ]
)

if lab_type == "Other":
    custom_lab_type = st.text_input("Enter the lab type")
    final_lab_type = custom_lab_type
else:
    final_lab_type = lab_type

experiment_title = st.text_input(
    "Experiment Title"
)

lab_goal = st.text_area(
    "What was the purpose or goal of the experiment?"
)

uploaded_files = st.file_uploader(
    "Upload Lab Files",
    type=["txt", "csv", "pdf", "docx"],
    accept_multiple_files=True
)

lab_data = st.text_area(
    "Paste observations, results, or notes here"
)

questions = st.text_area(
    "What would you like the AI to help with?",
    placeholder="Example: Interpret PCR bands, identify possible errors, explain results, write conclusion..."
)

# ---------------- FILE PROCESSING ---------------- #

def read_uploaded_file(uploaded_file):
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8")

    elif file_name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        return df.to_string()

    elif file_name.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    elif file_name.endswith(".docx"):
        document = docx.Document(uploaded_file)
        text = ""
        for para in document.paragraphs:
            text += para.text + "\n"
        return text

    else:
        return "Unsupported file type."


file_text = ""

if uploaded_files:
    for uploaded_file in uploaded_files:
        file_text += f"\n\n--- FILE: {uploaded_file.name} ---\n"
        file_text += read_uploaded_file(uploaded_file)

combined_data = f"""
Experiment Title:
{experiment_title}

Lab Type:
{final_lab_type}

Goal:
{lab_goal}

User Questions:
{questions}

Typed Observations:
{lab_data}

Uploaded File Data:
{file_text}
"""
# Button
# ---------------- CHAT HISTORY SETUP ---------------- #

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- MAIN AI RESPONSE ---------------- #

if "messages" not in st.session_state:
    st.session_state.messages = []

if st.button("Generate Lab Interpretation", key="generate_button"):

    prompt = f"""
    You are a biochemistry lab assistant.

    Lab Type:
    {final_lab_type}

    Goal:
    {lab_goal}

    Data:
    {combined_data}

    Write:
    1. Interpretation of the results
    2. Possible experimental errors
    3. A scientific conclusion
    4. Short explanation of the biochemical concepts involved
    """

    with st.spinner("Lab Folks AI is analyzing your lab data..."):

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response.choices[0].message.content
        }
    )

# ---------------- DISPLAY RESPONSES ---------------- #

for i, message in enumerate(st.session_state.messages):

    st.markdown(f"""
    <div style="
        background-color:#f8f9fa;
        padding:20px;
        border-radius:15px;
        border-left:6px solid #2E86C1;
        margin-bottom:20px;
        color:#111111;
    ">
        <h3>Lab Folks Response {i + 1}</h3>
        <p>{message["content"]}</p>
    </div>
    """, unsafe_allow_html=True)

    follow_up_question = st.text_area(
        f"Ask a follow-up question for Response {i + 1}",
        key=f"follow_up_box_{i}"
    )

    if st.button(
        f"Ask Follow-Up for Response {i + 1}",
        key=f"followup_button_{i}"
    ):

        follow_up_prompt = f"""
        You are a biochemistry lab assistant.

        Original lab information:
        {combined_data}

        Previous AI response:
        {message["content"]}

        Follow-up question:
        {follow_up_question}

        Answer the follow-up question clearly and scientifically.
        """

        with st.spinner("Generating follow-up analysis..."):

            follow_up_response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "user",
                        "content": follow_up_prompt
                    }
                ]
            )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": follow_up_response.choices[0].message.content
            }
        )

        st.rerun()
#streamlit run app.py