from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Document
from llama_index.core import VectorStoreIndex
from pinecone import Pinecone
from pinecone import ServerlessSpec
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import StorageContext
import openai
from llama_index.llms.openai import OpenAI
import torch
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core import get_response_synthesizer
from llama_index.core import PromptTemplate
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
import uuid
import json
import os
from llama_index.core.query_engine import RetrieverQueryEngine
from dotenv import load_dotenv

load_dotenv()
pc_index = 'askneu'
# Initialize Pinecone
pinecone_api_key = os.environ["pinecone_api"] 
pc = Pinecone(api_key=pinecone_api_key)
pinecone_index = pc.Index(pc_index)

# Initialize embeddings
Settings.embed_model = HuggingFaceEmbedding(
    model_name="Snowflake/snowflake-arctic-embed-m-v1.5", trust_remote_code=True
)

# Streamlit UI configuration
st.set_page_config(page_title="Ask NEU", layout="wide")

# Sidebar for API key and chat management
with st.sidebar:
    st.header("Configuration")
    openai_api_key = st.text_input("Enter OpenAI API Key:", type="password")
    
    st.markdown("---")
    st.header("Chat Management")
    
    # Initialize session state for chat management
    if "chats" not in st.session_state:
        st.session_state.chats = {}
    
    if "current_chat_id" not in st.session_state:
        chat_id = str(uuid.uuid4())
        st.session_state.current_chat_id = chat_id
        st.session_state.chats[chat_id] = {
            "id": chat_id,
            "title": "Chat 1 ",
            "history": []
        }
    
    # New Chat button
    if st.button("+ New Chat"):
        chat_id = str(uuid.uuid4())
        st.session_state.current_chat_id = chat_id
        st.session_state.chats[chat_id] = {
            "id": chat_id,
            "title": f"Chat {len(st.session_state.chats)+1}",
            "history": []
        }
    
    # Display existing chats
    st.subheader("Previous Chats")
    for chat_id in list(st.session_state.chats.keys()):
        if st.button(
            f"📝 {st.session_state.chats[chat_id]['title']}",
            key=f"chat_{chat_id}",
            use_container_width=True
        ):
            st.session_state.current_chat_id = chat_id

# Main chat interface
st.title("Ask NEU: Your AI Campus Companion")
st.markdown("Welcome to NEU Campus Info Chat Assistant!")

# Initialize current chat
current_chat = st.session_state.chats[st.session_state.current_chat_id]

# Display chat history
for message in current_chat["history"]:
    role = "Human" if isinstance(message, HumanMessage) else "AI"
    with st.chat_message(role):
        st.markdown(message.content)

# Chat input
user_query = st.chat_input("Type your question here...")

if user_query:
    if not openai_api_key:
        st.warning("Please enter your OpenAI API key in the sidebar!")
        st.stop()
    
    # Set OpenAI API key
    openai.api_key = openai_api_key
    Settings.llm = OpenAI(
        model="gpt-3.5-turbo",
        api_key=openai_api_key,
        request_timeout=360.0,
        temperature=0.3,
        num_beams=3
    )
    
    # Add user message to chat history
    current_chat["history"].append(HumanMessage(user_query))
    
    # Display user message
    with st.chat_message("Human"):
        st.markdown(user_query)
    
    # Initialize query engine components
    vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store, 
        embed_model=Settings.embed_model
    )
    
    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=10,
        embed_model=Settings.embed_model
    )
    
    qa_prompt = PromptTemplate(
        "You are a helpful assistant for Northeastern University queries.\n"
        "Context:\n{context_str}\n"
        "Question: {query_str}\nAnswer:"
    )
    
    response_synthesizer = get_response_synthesizer(
        response_mode="compact",
        llm=Settings.llm,
        text_qa_template=qa_prompt
    )
    
    query_engine = RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
    )
    
    # Generate response
    with st.spinner("Thinking..."):
        try:
            response = query_engine.query(user_query)
            ai_response = str(response)
        except Exception as e:
            ai_response = f"Error: {str(e)}"
    
    # Add and display AI response
    current_chat["history"].append(AIMessage(ai_response))
    with st.chat_message("AI"):
        st.markdown(ai_response)

