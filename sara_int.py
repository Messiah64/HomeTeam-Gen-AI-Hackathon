import streamlit_shadcn_ui as ui
import streamlit as st
import streamlit_book as stb
from openai import OpenAI
from PyPDF2 import PdfReader
import markdown
import re  # We'll use regex to strip out "Question1 - " if needed
from docx import Document
import io
import pdfkit  
import warnings

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
                "You are an expert Quiz Maker who makes thoughtful and fun quizzes. "
                "You never give the same type of questions twice. Understand this text "
                "and generate for 10 questions, 4 possible answers to each question, "
                "the correct answer's index( 0 to 3 as there are 4 options), and its reason "
                "for being correct or wrong. Each reason for each of the choices, depending "
                "on its correctness or wrongness. I want the Question, Choices, Correct Answer "
                "Index and Reasons to be in this format:\n\n"
                "Question1 | Choice1 | Choice2 | Choice3 | Choice4 | (example: 2 #For Choice 3) | "
                "(reason for option A) | (reason for option B) | (reason for option C) | (reason for option D)\n\n"
                "An Example if option C is the right answer: "
                "Question1 - What is the colour of healthy grass | Red | Yellow | Blue | Green | 3 | "
                "Healthy grass isn't Red colour | Grass is only yellow if its diseased | "
                "Its impossible for grass to be blue in colour | Yes! Grass is indeed Green in colour |\n\n"
                "Do not give me any other information other than this. STRICTLY follow this template I have specified. "
                "I dont want any filler words. DONT MESS THIS UP VERY IMPORTANT!! Use full content of my SOP book: "
                f"{user_query}\n\n"
                "Make sure to follow my specific structure of response. do not deviate from this at all."
            )
        }
    ]

    completion = client.chat.completions.create(
        model="o1-mini",
        messages=message_text, 
    )

    return completion.choices[0].message.content


@st.cache_resource
def OpenAI_Filtering_Check(input_text):
    OpenAI_Key = st.secrets["OpenAI_Key"]
    client = OpenAI(api_key=OpenAI_Key)

    message_text = [
        {
            "role": "system",
            "content": (
                "Take this input and Return this in a numbered bulletised format "
                "separated by the \\n key in between bullet points. Make sure no points "
                "that are given are the same. all must be unique. Omit if needed."
            )
        },
        {"role": "user", "content": input_text},
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

    return completion.choices[0].message.content


@st.cache_resource
def parse_questions_text(text):
    """
    Parses the AI's response line by line, expecting each line to have:
      0: question
      1-4: answer options
      5: correct answer index (1-based in the AI response)
      6-9: reasons for each option
    """
    questions = []
    answer_options = []
    correct_answer_index = []
    reasons = []

    for line in text.split("\n"):
        if line.strip():
            parts = line.split(" | ")

            # If the line does not have at least 10 parts, skip or raise error
            if len(parts) < 10:
                raise ValueError(
                    f"Line does not conform to required format:\n'{line}'"
                )

            # 1) Grab the question
            question_raw = parts[0].strip()

            # Optional: Clean up or remove the "QuestionX - " prefix if present
            # E.g. "Question1 - What is the colour of healthy grass"
            # We'll attempt a simple regex
            match = re.match(r"^(?:Question\s*\d+)?\s*[-–:]?\s*(.*)$", question_raw, re.IGNORECASE)
            if match:
                question = match.group(1).strip()
            else:
                question = question_raw

            # 2) Grab answer options (parts[1] to parts[4])
            options = [option.strip() for option in parts[1:5]]

            # 3) Grab correct answer index (make it 0-based for convenience)
            correct_index = int(parts[5].strip()) - 1

            # 4) Grab reasons for each option (parts[6] to parts[9])
            reason = [option.strip() for option in parts[6:10]]

            questions.append(question)
            answer_options.append(options)
            correct_answer_index.append(correct_index)
            reasons.append(reason)

    return questions, answer_options, correct_answer_index, reasons


st.markdown(
    """
    <style>
        /* Completely hide the MainMenu */
        #MainMenu { display: none; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("S.A.R.A :brain: :calendar: :zap:")
st.text("Structured Assesment & Review Aid")
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
    # 1) Read text from uploaded file
    pdf_text = read_pdf(uploaded_file)

    # 2) Keep retrying until parse is successful
    while True:
        response_message = get_chat_response(pdf_text)
        try:
            questions, answer_options, correct_answer_index, reasons = parse_questions_text(response_message)
            # If parsing succeeded, break out of loop
            break
        except ValueError as e:
            st.warning(f"Parsing failed (format mismatch). Retrying... \nError: {e}")
            continue

    # 3) Display each question using streamlit_book single_choice
    for i in range(len(questions)):
        # Debug: to confirm the question is actually parsed
        # st.write(f"**DEBUG QUESTION**: {questions[i]}")  # optional debug line

        def check_answer(selected_option):
            """
            If correct, display the reason plus all reason lines together (or however you want).
            If incorrect, show the reason for the selected option.
            """
            if selected_option == correct_answer_index[i] + 1:
                # Correct
                return (
                    f"{reasons[i][correct_answer_index[i]]} | "
                    f"{reasons[i][0]} | {reasons[i][1]} | {reasons[i][2]} | {reasons[i][3]}"
                )
            else:
                # Wrong
                return f"Option {selected_option}: {reasons[i][selected_option - 1]}"

        stb.single_choice(
            questions[i],                # The question text
            answer_options[i],           # The list of 4 answers
            correct_answer_index[i] + 1, # The correct choice (1-based for streamlit_book)
            success=OpenAI_Filtering_Check(
                check_answer(correct_answer_index[i] + 1)  # Explanation if correct
            ),
            error='Wrong Answer 😒 \n Please try again',     # Explanation if wrong
            button="Check answer"
        )
