# -*- coding: utf-8 -*-
"""
Created on Sun Mar  6 15:01:23 2022

@author: Lenovo
"""

import streamlit as st
import pyrebase
import pandas as pd
from datetime import datetime
from datetime import timedelta
import time
import pyttsx3
from PIL import Image



def countdown(deadline_time, timer_name, intro_msg, outro_msg = ''):
    pyttsx3.speak(intro_msg)
    with st.empty():
        while(True):
            now = datetime.now()
            if(deadline_time > now):
                st.metric(timer_name, str(deadline_time - now).split(".")[0])
                time.sleep(1)
            else:
                break
        
    pyttsx3.speak(outro_msg)
    
    
def submit_exam():
    for qid in st.session_state.saq_q_id:
        answer = {
            "exam_id" : st.session_state.examination_id,
            "sub_question_id" : qid,
            "student_id" : st.session_state.stud_id,
            "answer" : st.session_state[qid],
            "correct_keywords" : "",
            "reference_keywords" : "",
            "score" : 0,
            "verified" : 0
        }
        
        stud_info = {
            "student_id" : st.session_state.stud_id,
            "student_email" : st.session_state.stud_id + "@kdu-online.com",
            "student_name" : st.session_state.stud_name
        }
    
        st.session_state.db.child("student_answers").push(answer)
        st.session_state.db.child("student_information").child(st.session_state.stud_id).set(stud_info)
    
    st.success('All Answers submitted.')
    pyttsx3.speak("Examination submission confirmed. Thank you for taking the examination.")
    

def display_questions():
    line = '''
    ---
    '''
    # Get the examination data
    exam = st.session_state.db.child("exams").order_by_child("exam_id").equal_to(st.session_state.exam_id).get()
    
    qid = ''
    exam_title = ''
    start_time_ = ''
    duration = 0
    # Get examination info
    for e in exam.each():
        qid = e.val()['questions']
        exam_title = e.val()['exam_title']
        start_time_ = e.val()['date'] + ' ' + e.val()['start_time'] 
        duration = e.val()['duration_minutes']
                
    st.write(start_time_)
    q_num = 0
    question_number = []
    question_description = []
    total_marks = []
    num_of_subques = []
    subques = []
    # For each question id in the exam question id list,
    for q_id in qid:
        q_num += 1
        # Get the question data
        question = st.session_state.db.child('questions').order_by_child('question_id').equal_to(q_id).get()
    
        for q in question.each():
            question_number.append(q_num)
            question_description.append(q.val()['question_description'])
            total_marks.append(q.val()['total_marks'])
            num_of_subques.append(q.val()['num_of_subques'])
            subques.append(q.val()['sub_question_id'])
            if q.val()['total_marks'] > 1:
                m = "marks"
            else:
                m = "mark"
        
    # put the question data into a pandas dataframe
    questions = pd.DataFrame({'question_id': qid, 
                              'question_number': question_number, 
                              'question_description': question_description, 
                              'num_of_subques': num_of_subques, 
                              'total_marks': total_marks,
                              'm' : m})
    
    # Sort the question by question number
    questions.sort_values(by=["question_number"], inplace = True)
    start_time = datetime.strptime(start_time_, '%Y-%m-%d %H:%M:%S')
    now = datetime.now()
    end_time = datetime.strptime(start_time_, '%Y-%m-%d %H:%M:%S') + timedelta(minutes = duration)

    # Display the exam title
    st.header(exam_title)
    # Check if the examination has ended (if no then proceed with this block of code)
    if(end_time > now):
        col1, col2, col3 = st.columns(3)
        # Countdown to exam (if the student logs in before the examination starts)
        with col1:
            with st.spinner('Exam will begin soon...'):
                countdown(start_time, "Exam Starting In:", "Please wait until the examination starts.")
    
        # After the countdown has completed, or if the student joined on time or late, display the exam questions
        exam_form = st.form('exam_form')
        with exam_form:
            for index, row in questions.iterrows():
                saq = st.session_state.db.child("saq_sub_questions").order_by_child("sub_question_number").order_by_child("question_id").equal_to(row['question_id']).get()
        
                
                st.markdown('**Question ' + str(index + 1) + '**')
                if row['num_of_subques'] > 0:
                    if row['total_marks'] > 1:
                        ques = row['question_description'] + " (" + str(row['total_marks']) +" marks)"
                    else:
                        ques = row['question_description'] + " (" + str(row['total_marks']) +" mark)"
                    st.write(ques)
                
                if 'saq_q_id' not in st.session_state:
                    st.session_state.saq_q_id = []
                
                for s in saq.each():
                    saq_question_num = "(" + chr(s.val()['sub_question_number'] + 96) + ") "
                    saq_question_id = s.val()['sub_question_id']
                    saq_description = s.val()['sub_question_description']
                    saq_marks = s.val()['marks']
            
                    if row['num_of_subques'] == 0:
                        if row['total_marks'] > 1:
                            ques = row['question_description'] + " (" + str(row['total_marks']) +" marks)"
                        else:
                            ques = row['question_description'] + " (" + str(row['total_marks']) +" mark)"
                        st.write(ques)
                        st.text_area(label = '', key=saq_question_id)
                    else:
                        if saq_marks > 1:
                            ques = saq_question_num + saq_description + " (" + str(saq_marks) +" marks)"
                        else:
                            ques = saq_question_num + saq_description + " (" + str(saq_marks) +" mark)"
                        st.write(ques)
                        st.text_area(label = '', key=saq_question_id)
                    
                    st.session_state.saq_q_id.append(saq_question_id)
                
                st.markdown('\n\n')
                st.markdown(line)
            
            # A submit button to submit the exam
            btn_submit = st.form_submit_button('Submit Exam', on_click=submit_exam)
            
        with col2:
            # Exam timer - countdown towards the end of examination
            countdown(end_time, "Exam Time Left:", "You may begin the exam.")
            st.session_state.end = True
    
        with col3:
            # When examination countdown has completed, students are given two minites to submit their answers. 
            buffer_end_time = end_time + timedelta(minutes = 2)
            countdown(buffer_end_time, "Buffer Time:", "Time's up! Please tidy-up your answers and submit within the buffer time!", "The examination has ended. Thank you for taking the examination. Have a nice day ahead!")
        
    # If the student logs in after the examination has ended, display warning message 
    else:
        st.warning('The examination has ended. Please contact your teacher if you have missed the examination.')
        pyttsx3.speak('The examination has ended. Please contact your teacher if you have missed the examination.')
    
        
def verify_exam_login():
    # Check if inputs are empty
    if not st.session_state.student_id:
        st.error('Please Fill Up Your Student ID!')
    elif not st.session_state.student_name:
        st.error('Please Fill Up Your Student Name!')
    elif not st.session_state.exam_id:
        st.error('Please Fill Up the Exam ID!')
    elif not st.session_state.password:
        st.error('Please Fill Up the Exam Password!')
    else:
        if st.session_state.db.child('exams').child(st.session_state.exam_id).shallow().get().val():    
            # Get the exam dict from firebase real time database
            exam = st.session_state.db.child("exams").order_by_child("exam_id").equal_to(st.session_state.exam_id).get()
            
            # Assign session state variables
            if 'stud_id' not in st.session_state:
                st.session_state.stud_id = st.session_state.student_id
                
            if 'stud_name' not in st.session_state:
                st.session_state.stud_name = st.session_state.student_name
                
            if 'examination_id' not in st.session_state:
                st.session_state.examination_id = st.session_state.exam_id
                
            # Get the exam password
            pw = ''
            for e in exam.each():
                pw = e.val()['exam_password']
            # Check if password matches
            if st.session_state.password == pw:
                st.session_state.login = True
                st.write("")
                    
                # Display exam questions
                display_questions()
                
            else:
                st.error('Incorrect Password!')
        else:
            st.error("Incorrect Exam Id!")


def login_form():
    st.markdown("<h1 style='text-align: center; line-height: 120px;'>Online Exam Website</h1>", unsafe_allow_html=True)
    
    with st.form('login_exam'):
        st.header('Exam Login')
        st.text_input('Student ID: ', key='student_id')
        st.text_input('Student Name: ', key='student_name')
        st.text_input('Exam ID: ', key='exam_id')
        st.text_input('Exam Password: ', key='password')
        submit = st.form_submit_button('Submit', on_click=verify_exam_login)



# Firebase configuration
if 'config' not in st.session_state:
    # Firebase configurations
    st.session_state.config = {
        "apiKey": "AIzaSyB_kmIlFKKHu8HVPZEdFh1tiTQmX9lVOKg",
        "authDomain": "automated-exam-marking-system.firebaseapp.com",
        "databaseURL": "https://automated-exam-marking-system-default-rtdb.asia-southeast1.firebasedatabase.app",
        "projectId": "automated-exam-marking-system",
        "storageBucket": "automated-exam-marking-system.appspot.com",
        "messagingSenderId": "1097146013231",
        "appId": "1:1097146013231:web:c349e46afaa63957f4d8da",
        "measurementId": "G-RS9RM4LKC1"
    } 
    
if 'firebase' not in st.session_state:
    st.session_state.firebase = pyrebase.initialize_app(st.session_state.config)

if 'db' not in st.session_state:
    st.session_state.db = st.session_state.firebase.database()

if 'login' not in st.session_state:
    st.session_state.login = False
    

    
if not st.session_state.login:
    login_form()