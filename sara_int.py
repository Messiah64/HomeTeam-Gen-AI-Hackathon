import streamlit_shadcn_ui as ui
import streamlit as st
import streamlit_book as stb
from openai import OpenAI
from PyPDF2 import PdfReader
import markdown
from html2docx import html2docx
from docx import Document
import io
import pdfkit
import warnings
import re  # for extra checking if needed

warnings.filterwarnings("ignore")


@st.cache_resource
def read_pdf(file):
    pdf_reader = PdfReader(file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text += page.extract_text()
    return text


@st.cache_resource
def get_chat_response(user_query):
    OpenAI_Key = st.secrets["OpenAI_Key"]
    client = OpenAI(api_key=OpenAI_Key)

    message_text = [
        {
            "role": "user",
            "content": (
                f"You are an expert Quiz Maker who makes thoughtful and fun quizzes. "
                f"You never give the same type of questions twice. Understand this text and generate for 10 questions, "
                f"4 possible answers to each question, the correct answer's index (0 to 3 as there are 4 options), "
                f"and its reason for being correct or wrong. Each reason for each of the choices, depending on its correctness, "
                f"must be provided. I want the Question, Choices, Correct Answer Index and Reasons to be in this format:\n\n"
                f"Question1: <question text> ||| Choice1 ||| Choice2 ||| Choice3 ||| Choice4 ||| <correct index> ||| "
                f"Reason for choice 1 ||| Reason for choice 2 ||| Reason for choice 3 ||| Reason for choice 4\n\n"
                f"An Example if option C is the right answer:\n"
                f"Question1: What is the colour of healthy grass ||| Red ||| Yellow ||| Blue ||| Green ||| 3 ||| "
                f"Healthy grass isn't Red colour ||| Grass is only yellow if it's diseased ||| Its impossible for grass "
                f"to be blue in colour ||| Yes! Grass is indeed Green in colour\n\n"
                f"Do not give me any other information other than this. STRICTLY follow this template I have specified. "
                f"I dont want any filler words. DONT MESS THIS UP VERY IMPORTANT!! "
                f"Use full content of my SOP book: {user_query} . Remember to use my template I have provided."
            )
        }
    ]

    completion = client.chat.completions.create(
        model="o1-mini",
        messages=message_text,
    )

    filtered_message = completion.choices[0].message.content
    return filtered_message


@st.cache_resource
def OpenAI_Filtering_Check(input):
    OpenAI_Key = st.secrets["OpenAI_Key"]
    client = OpenAI(api_key=OpenAI_Key)

    message_text = [
        {
            "role": "system",
            "content": (
                "Take this input and return it in a numbered bulletised format separated by the \\n key "
                "between bullet points. Make sure no points are the same and all are unique. Omit if needed."
            )
        },
        {"role": "user", "content": input}
    ]

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=message_text,
        temperature=0.2,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )

    filtered_message = completion.choices[0].message.content
    return filtered_message


def parse_questions_text(text):
    """
    Parses the API response text.

    Expected format for each question (each on a separate line):
      QuestionX: <question text> ||| Choice1 ||| Choice2 ||| Choice3 ||| Choice4 ||| <correct index> ||| 
      Reason for choice 1 ||| Reason for choice 2 ||| Reason for choice 3 ||| Reason for choice 4

    For each non-empty line:
      - Splits the line on the delimiter "|||".
      - Trims extra spaces.
      - Verifies that exactly 10 parts exist.
      - Verifies that the correct answer index is a valid number.

    Returns:
      questions, answer_options, correct_answer_index, reasons
    """
    questions = []
    answer_options = []
    correct_answer_index = []
    reasons = []

    for line in text.splitlines():
        if line.strip():
            # Split the line using the custom delimiter "|||"
            parts = [p.strip() for p in line.split("|||") if p.strip()]
            if len(parts) != 10:
                raise ValueError(f"Line does not contain exactly 10 parts: {line}")
            question = parts[0]
            options = parts[1:5]
            correct_part = parts[5]
            if not correct_part.isdigit():
                raise ValueError(f"Expected a number for the correct answer index but got: {correct_part}")
            correct_idx = int(correct_part) - 1
            reason = parts[6:10]

            questions.append(question)
            answer_options.append(options)
            correct_answer_index.append(correct_idx)
            reasons.append(reason)

    return questions, answer_options, correct_answer_index, reasons


st.markdown(
    """
    <style>
        /* Completely hide the MainMenu */
        #MainMenu { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("S.A.R.A   &nbsp;&nbsp;:brain: :calendar: :zap:")
st.text("Structured Assessment & Review Aid")
st.text("No more fretting over upcoming Audits or Course Exams")
st.text("Stay up to date with new revised Standard Operating Procedure")

ui.badges(
    badge_list=[("Sentosa Fire Station", "destructive"), ("Life Saver Labs", "secondary")],
    class_name="flex gap-2",
    key="badges1"
)

uploaded_file = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx", "pptx"], label_visibility="collapsed")
st.divider()

if uploaded_file is not None:
    # Read text from the uploaded file
    pdf_text = read_pdf(uploaded_file)

    # --- Retry loop: call the API and try parsing up to 3 times ---
    max_attempts = 3
    attempt = 0
    parsed_successfully = False
    response_message = ""

    while attempt < max_attempts and not parsed_successfully:
        response_message = get_chat_response(pdf_text)
        print(response_message)  # For debugging: see the actual output
        try:
            questions, answer_options, correct_answer_index, reasons = parse_questions_text(response_message)
            parsed_successfully = True  # Parsing succeeded
        except Exception as e:
            attempt += 1
            st.warning(f"Parsing failed on attempt {attempt}: {e}. Retrying...")

    if not parsed_successfully:
        st.error("Failed to generate valid questions after 3 attempts. Please try again later.")
    else:
        st.success("Questions generated and parsed successfully!")
        # Display the questions using streamlit_book's single_choice widget
        for i in range(len(questions)):
            def check_answer(selected_option, idx=i):
                # Convert from 1-indexed selected_option to 0-indexed for comparison
                if selected_option == correct_answer_index[idx] + 1:
                    return f"{reasons[idx][correct_answer_index[idx]]}"
                else:
                    return f"Option {selected_option}: {reasons[idx][selected_option - 1]}"

            stb.single_choice(
                questions[i],
                answer_options[i],
                correct_answer_index[i] + 1,
                success=OpenAI_Filtering_Check(check_answer(correct_answer_index[i] + 1)),
                error="Wrong Answer 😒 \n Please try again",
                button="Check answer"
            )
