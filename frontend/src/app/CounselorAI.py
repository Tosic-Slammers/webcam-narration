from flask import Flask, jsonify, request
from flask_cors import CORS
import speech_recognition as sr
import requests
from dotenv import load_dotenv
import os
from model.mongoRAG import OpenAI_init_LLM, rag_template, conn_to_cluster, get_vectorstore, process

app = Flask(__name__)
CORS(app)  

# load environmental variables
load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MONGO_URI = os.getenv('MONGO_URI')

# Initialize the recognizer
r = sr.Recognizer()

# model initialization
llm = OpenAI_init_LLM()

# llm prompt initialization
custom_rag_prompt = rag_template()

# connect to mongodb
MONGODB_COLLECTION = conn_to_cluster(MONGO_URI)

# get vectorstore
vectorstore = get_vectorstore(MONGODB_COLLECTION)

@app.route('/counselorai', methods=['POST'])
def counselorai():
    text = request.json.get('text', '')
    llm_output = process(llm, vectorstore, text)
    response = jsonify({"text": "Therapist: " + llm_output})
    return response

@app.route('/speech_to_text', methods=['POST','GET'])
def speech_to_text():
    with sr.Microphone() as source:
        print("Calibrating for background noise. Please wait...")
        r.adjust_for_ambient_noise(source, duration=1)
        print("Please speak into the microphone.")
        # Starts listening
        audio = r.listen(source)
        # Finishes listening
        print("Processing audio...")
        try:
            text = r.recognize_google(audio)
            response = requests.post("http://127.0.0.1:5001/counselorai", json={"text": text})
            return jsonify({"message": "You: " + response.text})
        except Exception as e:
            return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(port=5001)
