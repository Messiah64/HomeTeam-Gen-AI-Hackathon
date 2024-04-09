import streamlit as st
import streamlit_book as stb
from openai import AzureOpenAI
from PyPDF2 import PdfReader

# Test 1

@st.cache_resource
def read_pdf(file):
    pdf_reader = PdfReader(file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text += page.extract_text()
    return text

@st.cache_resource
def parse_questions_text(text):
    lines = text.split("\n")  # Split text into lines
    questions = []
    answer_options = []
    correct_answer_index = []
    reasons = []

    for line in lines:
        if line.strip():  # Check if line is not empty
            parts = line.split(" | ")  # Split line by delimiter
            question_number = parts[0].strip()
            question = parts[1].strip()
            options = [option.strip() for option in parts[2:6]]  # Extract options
            correct_index = int(parts[-1].strip()) - 1  # Correct answer index is the last element
            reason = parts[-2].strip()[1:-1]  # Extract reason enclosed in brackets
            
            questions.append(f"{question_number} | {question}")
            answer_options.append(options)
            correct_answer_index.append(correct_index)
            reasons.append(reason)

    return questions, answer_options, correct_answer_index, reasons

@st.cache_resource
def get_chat_response(user_query):

    OpenAI_Key = st.secrets["OpenAI_Key"]

    # Initialize AzureOpenAI client
    client = AzureOpenAI(
        azure_endpoint="https://genai-llm.openai.azure.com/",
        api_key=OpenAI_Key,
        api_version="2024-02-15-preview"
    )

    # Create message text with system prompt and user query
    message_text = [
        {"role": "system", "content": "You are an expert Quiz Maker who makes thoughtful and unique quizzes. You never give the same type of questions twice. Understand this text and generate for 10 questions, 4 possible answers to each question, its reason for being correct, and the correct answer's index( 0 to 3 as there are 4 options) . I want the Question, Choices, Reason, Correnc answer index to be in this format: Question1 | Choice1 | Choice2 | Choice3 | Choice4 | (reason) | (example: 2 #For Choice 3). Do not give me any other information other than this. STRICTLY follow this template I have specified. i dont want any filler words. DONT MESS THIS UP VERY IMPORTANT!!"},
        {"role": "user", "content": "generate questions using full content of my SOP book: " + user_query}
    ]

    # Generate completion using AzureOpenAI API
    completion = client.chat.completions.create(
        model="GenAI-LLM",  # model = "deployment_name"
        messages=message_text,
        temperature=0.,
        max_tokens=10000,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )

    # Extract the filtered response message
    filtered_message = ""
    if completion.choices:
        for choice in completion.choices:
            if choice.message and choice.message.role == "assistant":
                filtered_message = choice.message.content
                break

    return filtered_message


def main():


    

    st.markdown(
        """
        # :red[S.A.R.A] &nbsp;&nbsp;:brain: :calendar: :zap:
        ### :blue[No more fretting over upcoming Audits or Course Exams]
        ### :blue[Stay up to date with new revised Standard Operating Procedure]
        """
    )
    st.divider()  #  Draws a horizontal rule

    # Set the label text
    label_text = "Upload the Standard Operating Procedures:"
    # Increase the size of the label using HTML styling
    st.markdown(f"<h5 style='color: #fcec04;'>{label_text}</h3>", unsafe_allow_html=True)

    # File uploader
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        
    # Start logic here
    # Read text from uploaded PDF file
        pdf_text = read_pdf(uploaded_file)
    
    # Pass the extracted text to the get_chat_response function
        response_message = get_chat_response(pdf_text)
        questions, answer_options, correct_answer_index, reasons = parse_questions_text(response_message)
        print(questions, answer_options, correct_answer_index, reasons)

        # st.write(response_message)
        for i in range(len(questions)):
            stb.single_choice(questions[i], answer_options[i], correct_answer_index[i] + 1, reasons[i], reasons[i])          
                  


if __name__ == "__main__":
    main()
