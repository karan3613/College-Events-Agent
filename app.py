import asyncio
from datetime import date

import pandas as pd
import streamlit as st
from pyparsing import empty

from NotificationHandler import NotificationHandler
from PineConeHandler import PineConeHandler

try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

@st.cache_resource
def load_models():
    """Initialize your models here"""
    pinecone_handler = PineConeHandler(index_name="")
    notification_handler = NotificationHandler(email = "" , password="")
    return pinecone_handler , notification_handler



def main():
    # Main title
    st.title("📅 Event Management System")
    st.markdown("---")

    if 'students' not in st.session_state:
        st.session_state.students = None


    pinecone_handler , notification_handler = load_models()

    # Create tabs
    tab1, tab2 = st.tabs(["🎯 Event Query Submission", "👥 Student Registration"])

    # Tab 1: Event Query Submission
    with tab1:
        st.header("📝 Submit Event Details")

        col1, col2 = st.columns(2)

        with col1:
            event_name = st.text_input("Event Name *", placeholder="Enter event name", key="event_name")
            event_prompt = st.text_area("Event Description", placeholder="Describe the event", key="event_desc")
            event_venue = st.text_input("Venue", placeholder="Event location", key="event_venue")

        with col2:
            event_date = st.date_input("Event Date", min_value=date.today(), key="event_date")
            event_time = st.time_input("Event Time", key="event_time")
            registration_deadline = st.date_input("Registration Deadline", max_value=event_date, key="reg_deadline")

        # Semester range
        st.subheader("Target Semesters")
        col3, col4 = st.columns(2)
        with col3:
            semester_from = st.selectbox("From Semester", [1, 2, 3, 4, 5, 6, 7, 8], key="sem_from")
        with col4:
            semester_to = st.selectbox("To Semester", [1, 2, 3, 4, 5, 6, 7, 8], index=7, key="sem_to")

        # Contact Information
        st.subheader("Contact Information")
        col5, col6 = st.columns(2)
        with col5:
            contact_person = st.text_input("Contact Person", placeholder="Name of organizer", key="contact_person")
            contact_email = st.text_input("Contact Email", placeholder="organizer@example.com", key="contact_email")
        with col6:
            contact_phone = st.text_input("Contact Phone", placeholder="+91 XXXXXXXXXX", key="contact_phone")
            department = st.text_input("Department/Club", placeholder="Organizing department", key="department")

        # Images and URLs
        st.subheader("Media and Links")
        uploaded_images = st.file_uploader("Upload Event Images",
                                           accept_multiple_files=True,
                                           type=['png', 'jpg', 'jpeg'],
                                           key="event_images")

        col7, col8 = st.columns(2)
        with col7:
            event_url = st.text_input("Event Registration URL", placeholder="https://example.com/register", key="event_url")
        with col8:
            additional_urls = st.text_area("Additional URLs (one per line)",
                                           placeholder="https://website.com\nhttps://social-media.com",
                                           key="additional_urls")

        # Submit button for events
        if st.button("📤 Submit Event", type="primary", key="submit_event" ,use_container_width=True):
            if event_name and contact_email and event_prompt:
                ############################################
                st.session_state.students = pinecone_handler.compare_embeddings(event_prompt=event_prompt , sem_to= semester_to , sem_from=semester_from)
                #############################################
                st.success("✅ Event submitted successfully!")
            else:
                st.error("❌ Please fill in at least Event Name and Contact Email")
        if st.session_state.students :
            st.header("Applicable Students")
            df = pd.DataFrame(st.session_state.students)
            st.dataframe(df, use_container_width=True)
            if st.button("📤 Send Email ", type="primary", key="submit_event" ,use_container_width=True):
                notification_handler.send_email(
                    images = uploaded_images ,
                    subject= f"{event_name} happening in your college on {event_date} at {event_venue}" ,
                    text_content=event_prompt ,
                    urls = event_url ,
                    recipients= [student['email'] for student in st.session_state.students]
                )
                st.success("✅ Emails sent successfully!")

    # Tab 2: Student Registration
    with tab2:
        st.header("👥 Student Registration")

        col1, col2 = st.columns(2)

        with col1:
            student_name = st.text_input("Full Name *", placeholder="Enter your full name", key="student_name")
            student_email = st.text_input("Email Address *", placeholder="student@example.com", key="student_email")
            student_phone = st.text_input("Phone Number", placeholder="+91 XXXXXXXXXX", key="student_phone")

        with col2:
            student_semester = st.selectbox("Semester *", [1, 2, 3, 4, 5, 6, 7, 8], key="student_semester")
            student_section = st.selectbox("Section *", ["A", "B", "C", "D", "E"], key="student_section")
            student_branch = st.selectbox("Branch/Department",
                                          ["Computer Science", "Information Technology", "Electronics", "Mechanical",
                                           "Civil", "Electrical", "Chemical", "Other"], key="student_branch")

        # Prompt for event preferences
        user_prompt = st.text_area("Describe the types of events you want to attend",
                                    placeholder="Tell us about your interests, preferred event types, topics you'd like to learn about, etc.",
                                    height=120,
                                    key="event_prompt")


        # Submit button for students
        if st.button("📝 Register Student", type="primary", key="submit_student" , use_container_width=True):
            if student_name and student_email and student_semester and student_section and user_prompt:
                #####################################################
                pinecone_handler.save_embdeddings(
                    user_prompt=user_prompt ,
                    email = student_email ,
                    username=student_name ,
                    sem = student_semester ,
                    section=student_section ,
                    branch= student_branch ,
                    mobile_no= student_phone
                )
                #######################################################
                st.success("✅ Student registration submitted successfully!")
            else:
                st.error("❌ Please fill in all required fields (marked with *)")

if __name__ == "__main__":
    main()