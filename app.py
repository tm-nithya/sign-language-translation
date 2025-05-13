from flask import Flask, render_template, redirect, request, url_for, send_file,jsonify
import mysql.connector
import os
import cv2
import speech_recognition as sr
import math
import numpy as np
from cvzone.HandTrackingModule import HandDetector
from keras.models import load_model
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet import preprocess_input
from flask import Flask, render_template, Response
from tensorflow.keras.preprocessing import image
from cvzone.ClassificationModule import Classifier
import subprocess
import torch
from ultralytics import YOLO
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from pynput import keyboard
from flask import make_response
import mediapipe as mp



app = Flask(__name__)

# Ensure upload folder exists
UPLOAD_FOLDER = "static/uploads/"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# MySQL Database Connection
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    port="3306",
    database='gesture'
)
mycursor = mydb.cursor()

def executionquery(query, values):
    mycursor.execute(query, values)
    mydb.commit()

def retrivequery1(query, values):
    mycursor.execute(query, values)
    data = mycursor.fetchall()
    return data

def retrivequery2(query):
    mycursor.execute(query)
    data = mycursor.fetchall()
    return data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        c_password = request.form['c_password']
        if password == c_password:
            query = "SELECT UPPER(email) FROM users"
            email_data = retrivequery2(query)
            email_data_list = [i[0] for i in email_data]
            if email.upper() not in email_data_list:
                query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
                values = (name, email, password)
                executionquery(query, values)
                return render_template('login.html', message="Successfully Registered!")
            return render_template('register.html', message="This email ID already exists!")
        return render_template('register.html', message="Confirm password does not match!")
    return render_template('register.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        query = "SELECT UPPER(email) FROM users"
        email_data = retrivequery2(query)
        email_data_list = [i[0] for i in email_data]
        if email.upper() in email_data_list:
            query = "SELECT UPPER(password) FROM users WHERE email = %s"
            values = (email,)
            password_data = retrivequery1(query, values)
            if password.upper() == password_data[0][0]:
                global user_email
                user_email = email
                return redirect("/home")
            return render_template('login.html', message="Invalid Password!")
        return render_template('login.html', message="This email ID does not exist!")
    return render_template('login.html')

@app.route('/home')
def home():
    response = make_response(render_template('home.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    print(response.headers)
    return response

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    return render_template('prediction.html')

@app.route('/graph')
def graph():
    return render_template('graph.html')

@app.route("/mic", methods=["GET", "POST"])
def mic():
    if request.method == "POST":
        # Check if a file is included in the request
        if "file" not in request.files:
            return jsonify({"error": "No file part in the request."})

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected for uploading."})

        try:
            # Perform transcription
            recognizer = sr.Recognizer()
            audioFile = sr.AudioFile(file)
            with audioFile as source:
                data = recognizer.record(source)
            transcript = recognizer.recognize_google(data, key=None)

            # Return the transcription result
            return jsonify({"transcript": transcript})
        except Exception as e:
            return jsonify({"error": str(e)})

    return render_template("mic.html", transcript1="")
    

@app.route('/open_webcam', methods=['POST', 'GET'])
def open_webcam():
    if request.method == 'POST':
        # Running demo.py when the form is submitted
        subprocess.Popen(['python', 'new.py'])

    return render_template('prediction.html')


@app.route('/sign', methods=['POST','GET'])
def sign():
    mpHands = mp.solutions.hands
    hands = mpHands.Hands(max_num_hands=1, min_detection_confidence=0.7)
    mpDraw = mp.solutions.drawing_utils

    # Load the gesture recognizer model
    model = load_model('mp_hand_gesture')

    # Load class names
    with open('gesture.names', 'r') as f:
        classNames = f.read().split('\n')
    print(classNames)

    # Initialize the webcam
    cap = cv2.VideoCapture(0)

    while True:
        # Read each frame from the webcam
        _, frame = cap.read()
        x, y, c = frame.shape

        # Flip the frame vertically
        frame = cv2.flip(frame, 1)
        framergb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Get hand landmark prediction
        result = hands.process(framergb)

        className = ''

        # Post-process the result
        if result.multi_hand_landmarks:
            landmarks = []
            for handslms in result.multi_hand_landmarks:
                for lm in handslms.landmark:
                    lmx = int(lm.x * x)
                    lmy = int(lm.y * y)
                    landmarks.append([lmx, lmy])

                # Draw landmarks
                mpDraw.draw_landmarks(frame, handslms, mpHands.HAND_CONNECTIONS)

                # Predict gesture
                prediction = model.predict([landmarks])
                classID = np.argmax(prediction)
                className = classNames[classID]
                print(className)

        # Display the prediction on the frame
        cv2.putText(frame, className, (10, 50), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 0, 255), 2, cv2.LINE_AA)

        # Show the final output
        cv2.imshow("Output", frame)

        if cv2.waitKey(1) == ord('q'):
            break

    # Release the webcam and close windows
    cap.release()
    cv2.destroyAllWindows()

    return render_template("prediction.html")

if __name__ == '__main__':
    app.run(debug=True)
