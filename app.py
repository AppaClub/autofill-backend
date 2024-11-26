# app.py

from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts.prompt import PromptTemplate
from langchain.document_loaders import PyPDFDirectoryLoader
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from flask import Flask, jsonify, request
from flask_cors import CORS
import asyncio
import os
from dotenv import load_dotenv
import math
import time

load_dotenv()

# Function to initialize and retrieve the language model from IBM Watson.
def get_llm():
    # Initialize Gemini LLM
    return ChatGoogleGenerativeAI(
        max_output_tokens=256,
        model="gemini-1.5-flash-8b",
        # model = "gemini-1.5-pro",
        temperature=0.2,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

# Function to process and index PDF documents.
def process_data():
    # Load PDF documents from a specified directory.
    loader = PyPDFDirectoryLoader("info")
    docs = loader.load()

    # Split the text from documents for better processing.
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=250, chunk_overlap=50)
    texts = text_splitter.split_documents(docs)

    # Create embeddings for the text data.
    embeddings = HuggingFaceInstructEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Index the documents using FAISS for efficient retrieval.
    db = FAISS.from_documents(texts, embeddings)
    return db
# Function to process a single field
async def process_field(field, llm_chain, db):
    # Retrieve relevant documents for the current field
    relevant_docs = db.similarity_search(field['label'], k=4)
    context = "\n".join([doc.page_content for doc in relevant_docs])
    question = field['label']
    additional_context = field.get('context', {})
    try:
        result = await llm_chain.arun(context=context, question=question)
        answer = result.strip()
        return {**field, "response": answer}
    except Exception as e:
        print(f"Error processing field '{field['label']}': {e}")
        return {**field, "response": ""}

# Function to automate form filling using the processed data.
async def filling_form(form_fields_info, batch_size = 4):
    llm = get_llm()
    db = process_data()

    prompt_template = PromptTemplate(
        input_variables=["context", "questions"],
        template="Human: Use the following context to answer these questions:\n\nContext: {context}\n\nQuestions:\n{questions}\n\nProvide concise answers for each question. If you arent sure of the answer, answer only NA\n\nAI: "
    )

    llm_chain = LLMChain(llm=llm, prompt=prompt_template)
    num_batches = math.ceil(len(form_fields_info) / batch_size)
    for i in range(num_batches):
        time.sleep(10)
        batch_fields = form_fields_info[i * batch_size:(i + 1) * batch_size]
        labels = " ".join([field['label'] for field in batch_fields])

    # Batch process all fields
        all_docs = db.similarity_search(labels, k=8)
        context = "\n".join([doc.page_content for doc in all_docs])

        questions = "\n".join([f"- {field['label']}" for field in batch_fields])
        print(f"Prompt sent to LLM:\nContext: {context}\nQuestions: {questions}")
        # print("-----------------------------------")

        result = await llm_chain.arun(context=context, questions=questions)

    # Parse the results
        answers = result.split("\n")
        structured_responses = []
        for field, answer in zip(batch_fields, answers):
            # Assuming the answer format is "Field Name: Value"
            # Split on the first occurrence of ": " to separate the field name from the value
            _, value = answer.split(": ", 1) if ": " in answer else ("", answer)
            structured_responses.append({**field, "response": value.strip()})  # Keep the field info and value
            # print(f"Responses:{structured_responses}")
    return structured_responses

# Initialize the Flask application for the web server.
app = Flask(__name__)
CORS(app)  # Enable cross-origin requests.

# Define API route to retrieve form data from the extension.
@app.route('/api/get_autofill_data', methods=['POST'])
async def get_autofill_data():
    form_fields_info = request.json.get('form_fields', [])
    structured_responses = await filling_form(form_fields_info)

    # Convert responses to a JSON format for the extension.
    response_data = {field['id']: field['response'] for field in structured_responses}
    return jsonify(response_data)


if __name__ == '__main__':

    app.run(debug=True, port=5055, host='0.0.0.0',load_dotenv=False)

