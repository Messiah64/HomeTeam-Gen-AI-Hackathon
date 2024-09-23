import streamlit as st
import streamlit_book as stb
from openai import OpenAI
import openai
from PyPDF2 import PdfReader

# Made by Khambhati 
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
    # openai.api_key = st.secrets["OpenAI_Key"]

    OpenAI_Key = st.secrets["OpenAI_Key"]
    client = OpenAI(api_key=OpenAI_Key)

    message_text = [
        {"role": "system", "content": "You are an expert Quiz Maker who makes thoughtful and fun quizzes. You never give the same type of questions twice. Understand this text and generate for 10 questions, 4 possible answers to each question, the correct answer's index( 0 to 3 as there are 4 options), and its reason for being correct or wrong. Each reason for each of the choices, depending its correct or wrong. I want the Question, Choices, Correct Answer Index and Reasons to be in this format: Question1 | Choice1 | Choice2 | Choice3 | Choice4 | (example: 2 #For Choice 3 | (reason for option A being correct/or wrong if not the right answer) | (reason for option B being correct/or wrong if not the right answer) | (reason for option C being correct/or wrong if not the right answer) | (reason for option D being correct/or wrong if not the right answer),   An Example if option C is the right answer: Question1 - What is the colour of healthy grass | Red | Yellow | Blue | Green | 3 | Healthy grass isn't Red colour | Grass is only yellow if its diseased | Its impossible for grass to be blue in colour | Yes! Grass is indeed Green in colour |. Do not give me any other information other than this. STRICTLY follow this template I have specified. i dont want any filler words. DONT MESS THIS UP VERY IMPORTANT!!"},
        {"role": "user", "content": "generate interesting questions using full content of my SOP book: " + user_query}
    ]

    completion = client.chat.completions.create(
        model="gpt-4o",
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
def OpenAI_Filtering_Check(input):

        OpenAI_Key = st.secrets["OpenAI_Key"]
        client = OpenAI(api_key=OpenAI_Key)

        message_text = [
            {"role": "system", "content": "Take this input and Return this in a numbered bulletised format seperated by the \n key in between bullet points. Make sure no points that are given are the same. all must be unique. Omit if needed."},
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

@st.cache_resource
def parse_questions_text(text):
    questions = []
    answer_options = []
    correct_answer_index = []
    reasons = []

    for line in text.split("\n"):
        if line.strip():
            parts = line.split(" | ")
            question = parts[0].strip()
            options = [option.strip() for option in parts[1:5]]
            correct_index = int(parts[5].strip()) - 1
            reason = [option.strip() for option in parts[6:10]]

            questions.append(question)
            answer_options.append(options)
            correct_answer_index.append(correct_index)
            reasons.append(reason)

    return questions, answer_options, correct_answer_index, reasons

def main():
    st.markdown(
        """
        # :red[S.A.R.A] &nbsp;&nbsp;:brain: :calendar: :zap:
        #### :blue[No more fretting over upcoming Audits or Course Exams]
        #### :blue[Stay up to date with new revised Standard Operating Procedure]
        """
    )
    st.divider()

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        # Read text from uploaded PDF file
        pdf_text = read_pdf(uploaded_file)
        # Pass the extracted text to the get_chat_response function
        response_message = get_chat_response(pdf_text)
        print(response_message)

        questions, answer_options, correct_answer_index, reasons = parse_questions_text(response_message)

        for i in range(len(questions)):
            def check_answer(selected_option):
                if selected_option == correct_answer_index[i] + 1:
                    return f"{reasons[i][correct_answer_index[i]]} | {reasons[i][0]} | {reasons[i][1]} | {reasons[i][2]} | {reasons[i][3]}"
                else:
                    return f"Option {selected_option}: {reasons[i][selected_option - 1]}"

            stb.single_choice(
                questions[i],
                answer_options[i],
                correct_answer_index[i] + 1,
                success=OpenAI_Filtering_Check(check_answer(correct_answer_index[i] + 1)),
                error='''Wrong Answer :) \n Please try again''',
                button="Check answer"
            )

if __name__ == "__main__":
    main()
    
