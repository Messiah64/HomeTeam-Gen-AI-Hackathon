import streamlit as st
import streamlit_book as stb

# Define the lists for questions, answer options, and correct answer indices
questions = [
    "What is the capital of France?",
    "Which planet is known as the Red Planet?",
    "Who wrote 'Romeo and Juliet'?",
    # Add more questions here as needed
]

answer_options = [
    ["Paris", "London", "Berlin", "Rome"],
    ["Mars", "Venus", "Jupiter", "Mercury"],
    ["William Shakespeare", "Jane Austen", "Charles Dickens", "Emily Brontë"],
    # Add more answer options lists here as needed
]

correct_answer_index = [
    0,  # For the first question, "Paris" is the correct answer
    2,  # For the second question, "Mars" is the correct answer
    0,  # For the third question, "William Shakespeare" is the correct answer
    # Add more correct answer indices here as needed
]


for i in range(len(questions)):
    stb.single_choice(questions[i], answer_options[i], correct_answer_index[i])

stb.single_choice("What does pandas (the library) stands for?",
                  ["The cutest bear", "Panel Data", 
                  "Pure Adamantium Numeric Datasets And Stuff", "PArties & DAtaSets"],
                  1)

