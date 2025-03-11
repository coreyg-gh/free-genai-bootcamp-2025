import streamlit as st
from app import JapaneseLearningApp

def main():
    st.set_page_config(
        page_title="Japanese Writing Practice",
        page_icon="✍️",
        layout="wide"
    )
    
    app = JapaneseLearningApp()
    app.run()

if __name__ == "__main__":
    main()