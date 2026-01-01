import streamlit as st
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import JSONLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

load_dotenv()

st.set_page_config(page_title="NBA Fantasy AI", layout="wide")
st.title("🏀 NBA Fantasy Chatbot")

# --- 1. VERİ YÜKLEME VE VERİTABANI (Sadece Başlangıçta) ---
@st.cache_resource # Veritabanını bir kez yükleyip bellekte tutar
def initialize_vector_store():
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    persist_dir = "nba_fantasy_db"
    
    # Eğer klasör yoksa veya boşsa verileri yükle
    if not os.path.exists(persist_dir) or not os.listdir(persist_dir):
        # JSON Yükleyiciler
        loaders = [
            JSONLoader(file_path='data/nba_fantasy_players.json', jq_schema='.[]', text_content=False),
            JSONLoader(file_path='data/nba_league_summary.json', jq_schema='.[]', text_content=False)
        ]
        data = []
        for loader in loaders:
            data.extend(loader.load())
            
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        docs = text_splitter.split_documents(data)
        
        vector_store = Chroma.from_documents(
            documents=docs, 
            embedding=embeddings, 
            persist_directory=persist_dir
        )
    else:
        vector_store = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
    
    return vector_store

vector_store = initialize_vector_store()
retriever = vector_store.as_retriever(search_kwargs={"k": 10})

# --- 2. MODELLER VE PROMPTLAR ---
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.3)

# Intent Classifier
intent_system_prompt = """Analyze the question and return ONLY ONE word: 
TRADE, STATS, GREETING, or GENERAL.
Question: {query}"""
intent_prompt = ChatPromptTemplate.from_template(intent_system_prompt)
intent_chain = intent_prompt | llm | StrOutputParser()

# Özelleştirilmiş Promptlar
stats_prompt_str = "You are an NBA Data Analyst. Find maximum values. Cite numbers.\nContext:\n{context}"
trade_prompt_str = "You are a Trade Consultant. Compare players. Say 'Accept' or 'Decline'.\nContext:\n{context}"
general_prompt_str = "You are a professional NBA Fantasy expert.\nContext:\n{context}"

# --- 3. ANA AKIŞ ---
query = st.text_input("Ask a question about NBA Fantasy Basketball:")

if query:
    with st.spinner("Analyzing intent and searching data..."):
        # Niyet Belirle
        intent = intent_chain.invoke({"query": query}).strip().upper()
        
        if "GREETING" in intent:
            st.info("👋 Hello! I am your NBA Fantasy assistant. You can ask me for player stats or trade advice!")
        else:
            # Doğru Promptu Seç
            if "TRADE" in intent:
                sys_prompt = trade_prompt_str
            elif "STATS" in intent:
                sys_prompt = stats_prompt_str
            else:
                sys_prompt = general_prompt_str
            
            # Dinamik Zincir Oluşturma
            qa_prompt = ChatPromptTemplate.from_messages([
                ("system", sys_prompt),
                ("user", "{input}"),
            ])
            
            qa_chain = create_stuff_documents_chain(llm, qa_prompt)
            rag_chain = create_retrieval_chain(retriever, qa_chain)
            
            # Yanıt Üret
            response = rag_chain.invoke({"input": query})
            
            st.caption(f"🛡️ Intent: {intent} Mode Activated")
            st.markdown(response["answer"])