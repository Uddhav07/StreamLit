import streamlit as st
import os
# from langchain_core.runnables import RunnablePassthrough
# from langchain_core.messages import HumanMessage
from langchain.document_loaders import UnstructuredFileLoader
# from langchain.document_loaders.image import UnstructuredImageLoader
from langchain.document_loaders import ImageCaptionLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# import pandas as pd
# from io import StringIO
from langchain.chains import ConversationalRetrievalChain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.llms import Ollama
import PyPDF2
from langchain_community.embeddings import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings()
# from langchain_community.embeddings import OllamaEmbeddings
# embeddings = OllamaEmbeddings()
from langchain_community.vectorstores import FAISS
# from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=50)
from langchain.chains.combine_documents import create_stuff_documents_chain


prompt = ChatPromptTemplate.from_template("""
Answer the following question based only on the provided context. 
Think step by step before providing a detailed answer. 
I will tip you $1000 if the user finds the answer helpful. 
<context>
{context}
</context>
Question: {input}""")

st.title("DocInsight")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


llm=Ollama(model="phi3")
output_parser=StrOutputParser()
# chain=prompt|llm|output_parser


document_chain=create_stuff_documents_chain(llm,prompt)

from langchain.chains import create_retrieval_chain

    
with st.sidebar:
    uploaded_files = st.file_uploader("Please upload your files", accept_multiple_files=True, type=None)
      
if uploaded_files:
    # Print the number of files uploaded or YouTube URL provided to the console
    st.write(f"Number of files uploaded: {len(uploaded_files)}")
        # Load the data and perform preprocessing only if it hasn't been loaded before
    if "processed_data" not in st.session_state:
        # Load the data from uploaded files
        documents = []

        if uploaded_files:
            for uploaded_file in uploaded_files:
                # Get the full file path of the uploaded file
                file_path = os.path.join(os.getcwd(), uploaded_file.name)

                # Save the uploaded file to disk
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())

                # Check if the file is an image
                if file_path.endswith((".png", ".jpg")):
                    # Use ImageCaptionLoader to load the image file
                    image_loader = ImageCaptionLoader(path_images=[file_path])

                    # Load image captions
                    image_documents = image_loader.load()

                    # Append the Langchain documents to the documents list
                    documents.extend(image_documents)
                    
                elif file_path.endswith((".pdf", ".docx", ".txt")):
                    # Use UnstructuredFileLoader to load the PDF/DOCX/TXT file
                    loader = UnstructuredFileLoader(file_path)
                    loaded_documents = loader.load()

                    # Extend the main documents list with the loaded documents
                    documents.extend(loaded_documents)

        # Chunk the data, create embeddings, and save in vectorstore
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
        document_chunks = text_splitter.split_documents(documents)

        vectorstore = FAISS.from_documents(document_chunks, embeddings)

        # Store the processed data in session state for reuse
        st.session_state.processed_data = {
            "document_chunks": document_chunks,
            "vectorstore": vectorstore,
        }

    else:
        # If the processed data is already available, retrieve it from session state
        document_chunks = st.session_state.processed_data["document_chunks"]
        vectorstore = st.session_state.processed_data["vectorstore"]
        
        
    if prompt := st.chat_input("Yooo wassup?"):
        
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # docs = db.similarity_search(prompt)
        
        retriever=vectorstore.as_retriever()
        retrieval_chain=create_retrieval_chain(retriever,document_chain)
        response=retrieval_chain.invoke({"input":prompt})
        
        
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response["answer"])
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response["answer"]})
