import os
import streamlit as st
from openai import AzureOpenAI


OpenAI_Key = st.secrets["OpenAI_Key"]

client = AzureOpenAI(
  azure_endpoint = "https://genai-llm.openai.azure.com/", 
  api_key=OpenAI_Key,  
  api_version="2024-02-15-preview"
)

message_text = [
    {"role": "system", "content": "You are an expert quiz maker. Di"},
    {"role": "user", "content": "are you gpt4?"}  # Example user message
]

completion = client.chat.completions.create(
    model="GenAI-LLM",  # model = "deployment_name"
    messages=message_text,
    temperature=0.7,
    max_tokens=800,
    top_p=0.95,
    frequency_penalty=0,
    presence_penalty=0,
    stop=None
)

# Assuming 'completion' contains the completion object
if completion.choices:
    for choice in completion.choices:
        if choice.message:
            actual_message = choice.message.content
            print(actual_message)
else:
    print("No completions found.")
