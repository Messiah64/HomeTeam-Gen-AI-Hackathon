import streamlit as st
from openai import OpenAI
from PyPDF2 import PdfReader
import streamlit_book as stb
import json
import warnings

warnings.filterwarnings("ignore")

# --------------------- OPENAI HELPER ---------------------
@st.cache_resource
def init_openai_client():
    """Initialize your custom OpenAI client."""
    OpenAI_Key = st.secrets["OpenAI_Key"]
    client = OpenAI(api_key=OpenAI_Key)
    return client

def call_openai_o1mini(user_content):
    """
    Makes a single chat completion call to the 'o1-mini' model
    using only user prompts (no system prompts).
    """
    client = init_openai_client()
    completion = client.chat.completions.create(
        model="o1-mini",
        messages=[{"role": "user", "content": user_content}],
    )
    return completion.choices[0].message.content

# --------------------- PDF READING -----------------------
@st.cache_resource
def read_pdf(file):
    pdf_reader = PdfReader(file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text += page.extract_text() or ""
    return text

# ------------------- STEP B: GENERATE QUESTIONS -------------------
def generate_questions(pdf_text):
    """
    1) Ask GPT to produce 10 quiz questions from the PDF text.
    2) Request strictly valid JSON with a 'questions' key.
    3) We'll embed the instructions in the user prompt (since no system prompt is allowed).
    """
    user_prompt = f"""
INSTRUCTIONS:
You are an expert quiz maker. You have the following text extracted from a PDF:

{pdf_text}

Generate exactly 10 quiz questions based on this text. Return the data
STRICTLY in this JSON format:

{{
  "questions": [
    {{
      "question_id": 1,
      "question_text": "..."
    }},
    {{
      "question_id": 2,
      "question_text": "..."
    }},
    ...
    {{
      "question_id": 10,
      "question_text": "..."
    }}
  ]
}}

No additional keys or text outside the JSON.
"""

    response_str = call_openai_o1mini(user_prompt)
    try:
        parsed = json.loads(response_str)
        questions = parsed.get("questions", [])
        return questions
    except (json.JSONDecodeError, KeyError):
        st.warning("Failed to parse questions from OpenAI.")
        return []

# ------------------- STEP C: GENERATE OPTIONS ---------------------
def generate_options(question_text, question_id):
    """
    For a single question, generate 4 distinct answer options.
    Return strictly valid JSON in the format:

    {
      "options": [
        "Option text 1",
        "Option text 2",
        "Option text 3",
        "Option text 4"
      ]
    }
    """
    user_prompt = f"""
INSTRUCTIONS:
You are an expert quiz maker. For the following question (ID: {question_id}),
generate exactly 4 distinct answer choices.

Return STRICTLY valid JSON with this structure:

{{
  "options": [
    "Choice A",
    "Choice B",
    "Choice C",
    "Choice D"
  ]
}}

No extra keys or text outside the JSON.

QUESTION:
{question_text}
"""
    response_str = call_openai_o1mini(user_prompt)
    try:
        parsed = json.loads(response_str)
        options = parsed.get("options", [])
        return options
    except (json.JSONDecodeError, KeyError):
        st.warning(f"Failed to parse options for question {question_id}")
        return []

# ------- STEP D: DETERMINE CORRECT ANSWER + REASONS -------
def generate_correct_and_reasons(question_text, options, question_id):
    """
    For each question+4 options, determine which option is correct
    (0-indexed) and provide the reason for each option.

    Return JSON:
    {
      "correct_index": <0-3>,
      "reasons": [
        "Reason for option 0",
        "Reason for option 1",
        "Reason for option 2",
        "Reason for option 3"
      ]
    }
    """
    # Build a user prompt with instructions + the question + the 4 options
    options_list_str = "\n".join([f"{idx}) {opt}" for idx, opt in enumerate(options)])
    user_prompt = f"""
INSTRUCTIONS:
You are an expert quiz maker. You have a question with four options.
Return STRICTLY valid JSON in the format:

{{
  "correct_index": 0,
  "reasons": [
    "Reason for option 0",
    "Reason for option 1",
    "Reason for option 2",
    "Reason for option 3"
  ]
}}

Where "correct_index" is an integer between 0 and 3 indicating the right option,
and "reasons" contains the explanations for each option's correctness or incorrectness.
No extra keys or text outside the JSON.

QUESTION (ID: {question_id}):
{question_text}

OPTIONS:
{options_list_str}
"""

    response_str = call_openai_o1mini(user_prompt)
    try:
        parsed = json.loads(response_str)
        correct_index = parsed.get("correct_index", 0)
        reasons = parsed.get("reasons", ["", "", "", ""])
        return correct_index, reasons
    except (json.JSONDecodeError, KeyError):
        st.warning(f"Failed to parse correct_index/reasons for question {question_id}")
        return 0, ["", "", "", ""]

# -------------- CHAIN EVERYTHING TOGETHER ---------------
def compile_quiz(pdf_text):
    """
    1) Generate 10 questions
    2) For each question, generate 4 options
    3) For each question+options, determine correct_index + reasons
    4) Return a list of dict objects with all relevant info
    """
    quiz_data = []
    questions = generate_questions(pdf_text)

    for q in questions:
        question_id = q.get("question_id", 0)
        question_text = q.get("question_text", "")

        # Step C: 4 answer options
        options = generate_options(question_text, question_id)

        # Step D: correct index + reasons
        correct_idx, reasons = generate_correct_and_reasons(question_text, options, question_id)

        quiz_data.append({
            "question_id": question_id,
            "question_text": question_text,
            "options": options,
            "correct_index": correct_idx,
            "reasons": reasons
        })

    return quiz_data

# ------------------ STREAMLIT MAIN APP -------------------
def main():
    st.title("S.A.R.A (Structured Assessment & Review Aid)")

    uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
    if uploaded_file is not None:
        pdf_text = read_pdf(uploaded_file)

        with st.spinner("Generating quiz..."):
            quiz_data = compile_quiz(pdf_text)

        st.success("Quiz generated! Scroll down to start answering.")

        # Render each question using streamlit_book
        for item in quiz_data:
            question_text = item["question_text"]
            options = item["options"]
            correct_idx = item["correct_index"]
            reasons = item["reasons"]

            # streamlit_book's single_choice is 1-indexed for correct answer
            stb.single_choice(
                question_text,
                options,
                correct_idx + 1,  # +1 because streamlit_book expects 1-based index
                success=reasons[correct_idx],  # show reason for the correct one
                error="Oops, that's not correct. Try again!",
                button="Check answer"
            )

if __name__ == "__main__":
    main()
