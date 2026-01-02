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

st.title("🏀 NBA Fantasy Chatbot")

player_loader = JSONLoader(
    file_path='data/nba_fantasy_players.json',
    jq_schema='.[]',
    text_content=False
)
player_data = player_loader.load()

team_loader = JSONLoader(
    file_path='data/nba_league_summary.json',
    jq_schema='.[]',
    text_content=False
)
team_data = team_loader.load()

data = player_data + team_data

# Chunking işlemi aslında gereksiz çünkü zaten 452 data var bunları hiç ayırmıyor.
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, 
    chunk_overlap=0
)

docs = text_splitter.split_documents(data)

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

vector_store = Chroma(
    embedding_function=embeddings,
    persist_directory="nba_fantasy_db"
)

retriever = vector_store.as_retriever(search_kwargs={"k": 10})

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.3,max_tokens=500)

intent_system_prompt = """Analyze the question and return ONLY ONE word: 
TRADE, STATS, GREETING, or GENERAL.
Question: {query}"""
intent_prompt = ChatPromptTemplate.from_template(intent_system_prompt)
intent_chain = intent_prompt | llm | StrOutputParser()

stats_prompt_str = """You are an NBA Data Analyst. Your goal is to provide precise statistical rankings.

Follow these steps:
1. Extract all players and their relevant numeric values (e.g., AVG_PTS, TOTAL_REB) from the provided Context.
2. Convert these text-based numbers into a mental list and SORT them numerically (Descending/Ascending as requested).
3. If the user asks for "top" or "highest", provide the top results based on your sorted list.
4. Always cite the exact numbers for each player mentioned.
5. If the data for a specific player is not in the context, state that you don't have that information.

Context:
{context}

Question: {input}"""
trade_prompt_str = """You are a professional NBA Fantasy Trade Consultant. 
Use the provided Context to analyze trades and team needs.

CORE INSTRUCTIONS:
1. IF TWO PLAYERS ARE PROVIDED: Compare their statistics (AVG_PTS, AVG_REB, AVG_AST, AVG_ST, AVG_BLK, FG_PCT, etc.). Analyze who wins the trade based on which categories they improve. Say 'Accept' or 'Decline' at the end.
2. IF USER ASKS FOR A 'FAIR TRADE': Look through the Context for players who have similar statistical profiles (e.g., similar AVG_PTS and similar roles). Suggest 2-3 names that would be a fair swap based on their overall contribution.
3. IF USER WANTS TO IMPROVE A SPECIFIC STAT (e.g., "I need more blocks"): 
   - Identify players in the Context who have high values in that specific category (e.g., high AVG_BLK).
   - Suggest a strategic swap: "Trade a player with high AVG_AST for a player with high AVG_BLK if you need defensive stats."

CONSTRAINTS:
- Use ONLY the provided Context data. No external NBA knowledge.
- If you don't have enough players in the Context to make a suggestion, say so.
- Be concise and strategic.

Context:
{context}

Question: {input}"""
general_prompt_str = "You are a professional NBA Fantasy expert.\nContext:\n{context}"

query = st.text_input("Ask a question about NBA Fantasy Basketball:")

if query:
    with st.spinner("Analyzing intent and searching data..."):
        # Niyet Belirle
        intent = intent_chain.invoke({"query": query}).strip().upper()
        
        if "GREETING" in intent:
            st.info("Hello! I am your NBA Fantasy assistant. You can ask me for player stats or trade advice!")
        else:
            # Uygun Promptu Seç
            if "TRADE" in intent:
                sys_prompt = trade_prompt_str
            elif "STATS" in intent:
                sys_prompt = stats_prompt_str
            else:
                sys_prompt = general_prompt_str
            
            qa_prompt = ChatPromptTemplate.from_messages([
                ("system", sys_prompt),
                ("user", "{input}"),
            ])
            
            qa_chain = create_stuff_documents_chain(llm, qa_prompt)
            rag_chain = create_retrieval_chain(retriever, qa_chain)
            
            # Yanıt Üret
            response = rag_chain.invoke({"input": query})
            
            if intent == "STATS":
                st.caption("Statistical analysis")
            elif intent == "TRADE":
                st.caption("Trade evaluation")

            st.markdown(response["answer"])