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

warnings.filterwarnings("ignore")

# =========================
#       HELPER FUNCTIONS
# =========================

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
    """
    Generate quiz questions & answers for EMT Training Dojo.
    """
    OpenAI_Key = st.secrets["OpenAI_Key"]
    client = OpenAI(api_key=OpenAI_Key)

    message_text = [ 
        
        {
            "role": "user",
            "content": (
                "You are an expert Quiz Maker who makes thoughtful and fun quizzes. "
                "You never give the same type of questions twice. Understand this text and "
                "generate for 10 questions, 4 possible answers to each question, the correct "
                "answer's index(0 to 3 as there are 4 options), and its reason for being correct "
                "or wrong. Each reason for each of the choices, depending its correct or wrong. "
                "I want the Question, Choices, Correct Answer Index and Reasons to be in this format: "
                "Question1 | Choice1 | Choice2 | Choice3 | Choice4 | (example: 2 #For Choice 3 | "
                "(reason for option A being correct/or wrong if not the right answer) | "
                "(reason for option B being correct/or wrong if not the right answer) | "
                "(reason for option C being correct/or wrong if not the right answer) | "
                "(reason for option D being correct/or wrong if not the right answer). "
                "An Example if option C is the right answer: "
                "Question1 - What is the colour of healthy grass | Red | Yellow | Blue | Green | 3 | "
                "Healthy grass isn't Red colour | Grass is only yellow if its diseased | "
                "Its impossible for grass to be blue in colour | Yes! Grass is indeed Green in colour |. "
                "Do not give me any other information other than this. STRICTLY follow this template "
                "I have specified. I dont want any filler words. DONT MESS THIS UP VERY IMPORTANT!! "
                "Use full content of my SOP book: "
                f"{user_query}"
            )
        }
    ]

    completion = client.chat.completions.create(
        model="o1-preview",
        messages=message_text
    )

    filtered_message = completion.choices[0].message.content
    return filtered_message

@st.cache_resource
def get_psct_chat_response(user_query):
    """
    Generate quiz questions & answers for PSCT Training Dojo.
    """
    OpenAI_Key = st.secrets["OpenAI_Key"]
    client = OpenAI(api_key=OpenAI_Key)

    message_text = [
        {
            "role": "system",
            "content": (
                "You are an expert Quiz Maker who makes thoughtful and fun quizzes. "
                "You never give the same type of questions twice. Understand this question and "
                "answer and reasoning, and generate for 10 PARAGRAPH LONG ELABORATE SCENARIO "
                "questions without ECG based on the similar questioning style as given information, "
                "4 possible answers to each question, the correct answer's index(0 to 3 as there "
                "are 4 options), and its reason for being correct or wrong. Each reason for each "
                "of the choices, depending its correct or wrong. I want the Question, Choices, "
                "Correct Answer Index and Reasons to be in this format: "
                "Question1 | Choice1 | Choice2 | Choice3 | Choice4 | (example: 2 #For Choice 3 | "
                "(reason for option A being correct/or wrong if not the right answer) | "
                "(reason for option B being correct/or wrong if not the right answer) | "
                "(reason for option C being correct/or wrong if not the right answer) | "
                "(reason for option D being correct/or wrong if not the right answer). "
                "An Example if option C is the right answer: "
                "Question1 - What is the colour of healthy grass | Red | Yellow | Blue | Green | 3 | "
                "Healthy grass isn't Red colour | Grass is only yellow if its diseased | "
                "Its impossible for grass to be blue in colour | Yes! Grass is indeed Green in colour |. "
                "Do not give me any other information other than this. STRICTLY follow this template "
                "I have specified. I dont want any filler words. DONT MESS THIS UP VERY IMPORTANT!!"
            )
        },
        {
            "role": "user",
            "content": "generate interesting questions using full content of my SOP book: " + user_query
        }
    ]

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=message_text,
        temperature=0.9,
        top_p=0.5,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )

    filtered_message = completion.choices[0].message.content
    return filtered_message

@st.cache_resource
def OpenAI_Filtering_Check(input_text):
    """
    Filter or transform text into bulletized format using GPT.
    """
    OpenAI_Key = st.secrets["OpenAI_Key"]
    client = OpenAI(api_key=OpenAI_Key)

    message_text = [
        {
            "role": "system",
            "content": (
                "Take this input and Return this in a numbered bulletised format separated by "
                "the \\n key in between bullet points. Make sure no points that are given are "
                "the same. all must be unique. Omit if needed."
            )
        },
        {
            "role": "user",
            "content": input_text
        }
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

@st.cache_resource
def parse_questions_text(text):
    """
    Extract question, options, correct index, and reasons from
    the response text that is in a specific '|' delimited format.
    """
    questions = []
    answer_options = []
    correct_answer_index = []
    reasons = []

    for line in text.split("\n"):
        if line.strip():
            parts = line.split(" | ")
            question = parts[0].strip()
            options = [option.strip() for option in parts[1:5]]
            correct_index = int(parts[5].strip()) - 1  # shift to 0-based
            reason = [option.strip() for option in parts[6:10]]

            questions.append(question)
            answer_options.append(options)
            correct_answer_index.append(correct_index)
            reasons.append(reason)

    return questions, answer_options, correct_answer_index, reasons

def generate_docx(text):
    """
    Creates a DOCX file from the provided text and provides
    a download button to save it locally.
    """
    doc = Document()
    doc.add_paragraph(text)

    # Save the docx file in a BytesIO object
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)

    # Generate download button
    st.download_button(
        label="Download .docx",
        data=file_stream,
        file_name="output.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

def generate_test_questions(question_quantity, pdf_text, option):
    """
    Generate new quiz questions (EMT Test Mode).
    """
    OpenAI_Key = st.secrets["OpenAI_Key"]
    client = OpenAI(api_key=OpenAI_Key)

    message_text = [
        {
            "role": "user",
            "content": (
                f"You are an expert Quiz Maker who makes thoughtful and fun quizzes. You never give "
                f"the same type of questions twice and always return them in neat formatted style. "
                f"Understand this text and generate for me {question_quantity} {option} questions, "
                f"4 possible answers to each question first. Then return each question's correct "
                f"answer index(1 to 4 as there are 4 options) and the reason why its correct. I want "
                f"the Question, Choices and then Correct Answer Index and Reasons to be in this format: "
                f"Question1 -(each option to have a checkbox for user to tick and be in numbered bulletised format) "
                f"Choice1 Choice2 Choice3 Choice4. once questions are finished generating, then start with the answers. "
                f"Answers - 1: A Reason: <its reason>, 2: B Reason: <its reason>, 3: D Reason: <its reason> and so on. "
                f"Do not give me any other information other than this. STRICTLY follow this template I have specified "
                f"(list out all the questions first, then their answers in the specified format). i dont want any filler words. "
                f"DONT MESS THIS UP VERY IMPORTANT!!{pdf_text}"
            )
        }
    ]

    completion = client.chat.completions.create(
        model="o1-preview",
        messages=message_text
    )

    filtered_message = completion.choices[0].message.content

    if not filtered_message:
        st.error("Failed to generate questions.")
    else:
        st.success("Questions generated successfully.")

    generate_docx(filtered_message)

def generate_psct_test_questions(question_quantity, pdf_text, option):
    """
    Generate new quiz questions (PSCT Test Mode).
    """
    OpenAI_Key = st.secrets["OpenAI_Key"]
    client = OpenAI(api_key=OpenAI_Key)

    message_text = [
        {
            "role": "user",
            "content": 
                f"You are an expert Quiz Maker who makes thoughtful and fun quizzes. You never give the same "
                f"type of questions twice and always return them in neat formatted style. Understand this text "
                f"and generate for me {option} questions, 4 possible answers to each question first. Then "
                f"return each question's correct answer index(1 to 4 as there are 4 options) and the reason "
                f"why its correct. I want the Question, Choices and then Correct Answer Index and Reasons to "
                f"be in this format: Question1 -(each option to have a checkbox for user to tick and be in "
                f"numbered bulletised format) Choice1 Choice2 Choice3 Choice4. once questions are finished "
                f"generating, then start with the answers. Answers - 1: A Reason: <its reason>, 2: B Reason: "
                f"<its reason>, 3: D Reason: <its reason> and so on. Do not give me any other information other "
                f"than this. STRICTLY follow this template I have specified(list out all the questions first, then "
                f"their answers in the specified format). i dont want any filler words. DONT MESS THIS UP VERY "
                f"IMPORTANT!!""generate these many questions: " + question_quantity + " using this information: " + pdf_text
        }
    ]

    completion = client.chat.completions.create(
        model="o1-preview",
        messages=message_text,
        temperature=0.9,
        max_tokens=1000,
        top_p=0.5,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )

    filtered_message = completion.choices[0].message.content

    if not filtered_message:
        st.error("Failed to generate questions.")
    else:
        st.success("Questions generated successfully.")

    generate_docx(filtered_message)

# =========================
#    STREAMLIT FRONTEND
# =========================

st.title("S.A.R.A   :brain: :calendar: :zap:")
st.text("Structured Assesment & Review Aid")
st.text("No more fretting over upcoming Audits or Course Exams")
st.text("Stay up to date with new revised Standard Operating Procedure")

ui.badges(
    badge_list=[("Lifesaver Labs", "secondary"), ("Sentosa Fire Station", "destructive")],
    class_name="flex gap-2",
    key="badges1"
)

uploaded_file = st.file_uploader(
    "Upload PDF or DOCX",
    type=["pdf", "docx", "pptx"],
    label_visibility="collapsed"
)

st.divider()

# Tabs at the top: 4 options
selected_tab = ui.tabs(
    options=["EMT Training Dojo", "PSCT Training Dojo", "EMT Test Mode", "PSCT Test Mode"],
    default_value='EMT Training Dojo',
    key="main_tabs"
)

if uploaded_file is not None:
    # ======== EMT TRAINING DOJO ========
    if selected_tab == 'EMT Training Dojo':
        pdf_text = read_pdf(uploaded_file)
        response_message = get_chat_response(pdf_text)
        print(response_message)

        questions, answer_options, correct_answer_index, reasons = parse_questions_text(response_message)

        for i in range(len(questions)):
            def check_answer(selected_option):
                if selected_option == correct_answer_index[i] + 1:
                    # If correct
                    return (
                        f"{reasons[i][correct_answer_index[i]]} | "
                        f"{reasons[i][0]} | {reasons[i][1]} | {reasons[i][2]} | {reasons[i][3]}"
                    )
                else:
                    # If incorrect
                    return f"Option {selected_option}: {reasons[i][selected_option - 1]}"

            stb.single_choice(
                questions[i],
                answer_options[i],
                correct_answer_index[i] + 1,
                success=OpenAI_Filtering_Check(check_answer(correct_answer_index[i] + 1)),
                error='''Wrong Answer 😒 \n Please try again''',
                button="Check answer"
            )

    # ======== PSCT TRAINING DOJO ========
    elif selected_tab == 'PSCT Training Dojo':
        pdf_text = read_pdf(uploaded_file)
        response_message = get_psct_chat_response(pdf_text)
        print(response_message)

        questions, answer_options, correct_answer_index, reasons = parse_questions_text(response_message)

        for i in range(len(questions)):
            def check_answer(selected_option):
                if selected_option == correct_answer_index[i] + 1:
                    return (
                        f"{reasons[i][correct_answer_index[i]]} | "
                        f"{reasons[i][0]} | {reasons[i][1]} | {reasons[i][2]} | {reasons[i][3]}"
                    )
                else:
                    return f"Option {selected_option}: {reasons[i][selected_option - 1]}"

            stb.single_choice(
                questions[i],
                answer_options[i],
                correct_answer_index[i] + 1,
                success=OpenAI_Filtering_Check(check_answer(correct_answer_index[i] + 1)),
                error='''Wrong Answer 😒 \n Please try again''',
                button="Check answer"
            )

    # ======== EMT TEST MODE ========
    elif selected_tab == 'EMT Test Mode':
        question_quantity = st.text_input("**Enter number of questions:**", placeholder="30", key="question_quantity")
        option = st.selectbox(
            "**Choose your difficulty level**",
            ("Easy", "Moderate", "Difficulty"),
        )
        st.write("You selected:", option)

        generate_button_clicked = st.button("Generate", key="generate_button")
        if generate_button_clicked:
            if question_quantity and question_quantity.strip() != "":
                st.write(f"Number of questions to generate: {question_quantity}")
                pdf_text = read_pdf(uploaded_file)
                generate_test_questions(question_quantity, pdf_text, option)
            else:
                st.write("Please enter a valid number.")

    # ======== PSCT TEST MODE ========
    elif selected_tab == 'PSCT Test Mode':
        question_quantity = st.text_input("**Enter number of questions:**", placeholder="30", key="question_quantity")
        option = st.selectbox(
            "**Choose your difficulty level**",
            ("Easy", "Moderate", "Difficulty"),
        )
        st.write("You selected:", option)

        generate_button_clicked = st.button("Generate", key="generate_button")
        if generate_button_clicked:
            if question_quantity and question_quantity.strip() != "":
                st.write(f"Number of questions to generate: {question_quantity}")
                pdf_text = read_pdf(uploaded_file)
                generate_psct_test_questions(question_quantity, pdf_text, option)
            else:
                st.write("Please enter a valid number.")
