# app.py

# Import required libraries
# from ibm_watson_machine_learning.foundation_models.extensions.langchain import WatsonxLLM
# from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
# from ibm_watson_machine_learning.foundation_models import Model

from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts.prompt import PromptTemplate

from langchain.document_loaders import PyPDFDirectoryLoader
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from flask import Flask, jsonify, request
from flask_cors import CORS

import os
from dotenv import load_dotenv

load_dotenv()

# Function to initialize and retrieve the language model from IBM Watson.
def get_llm():
    # Initialize Gemini LLM
    return ChatGoogleGenerativeAI(
        model="gemini-pro",
        temperature=0.0,
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

# Function to automate form filling using the processed data.
def filling_form(form_fields_info):
    # Initialize the language model and data processing tools.
    llm = get_llm()
    db = process_data()

    # Create a prompt template that includes both the question and the context
    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template="Human: Use the following context to answer the question:\n\nContext: {context}\n\nQuestion: Based on the document, what is the '{question}'? Provide only the required information.\n\nAI: "
    )

    # Create an LLMChain
    llm_chain = LLMChain(llm=llm, prompt=prompt_template)

    structured_responses = []
    for field in form_fields_info:
        # Retrieve relevant documents
        docs = db.similarity_search(field['label'], k=4)
        context = "\n".join([doc.page_content for doc in docs])

        # Get the response for each field
        result = llm_chain.run(context=context, question=field['label'])
        structured_responses.append({**field, "response": result.strip()})

    return structured_responses

# Initialize the Flask application for the web server.
app = Flask(__name__)
CORS(app)  # Enable cross-origin requests.

# Define API route to retrieve form data from the extension.
@app.route('/api/get_autofill_data', methods=['POST'])
def get_autofill_data():
    form_fields_info = request.json.get('form_fields', [])
    structured_responses = filling_form(form_fields_info)

    # Convert responses to a JSON format for the extension.
    response_data = {field['id']: field['response'] for field in structured_responses}
    return jsonify(response_data)


if __name__ == '__main__':

    app.run(debug=True, port=5055, host='0.0.0.0',load_dotenv=False)

