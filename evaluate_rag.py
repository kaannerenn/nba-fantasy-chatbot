import os
import time
from dotenv import load_dotenv
from datasets import Dataset

from ragas import evaluate
from ragas.metrics import faithfulness, context_recall

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings
)
from langchain_chroma import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001"
)

vector_store = Chroma(
    persist_directory="nba_fantasy_db",
    embedding_function=embeddings
)

retriever = vector_store.as_retriever(
    search_kwargs={"k": 10}  
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0
)

system_prompt = """
You are an NBA fantasy basketball expert.
Answer the question using ONLY the provided context.
If the answer is not in the context, say "I don't know".

Context:
{context}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "{input}")
])

qa_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, qa_chain)

intent_prompt = ChatPromptTemplate.from_template("""
Analyze the question and return ONLY ONE word:
STATS, TRADE, GENERAL
Question: {query}
""")

intent_chain = intent_prompt | llm | StrOutputParser()

test_set = [
    {
        "question": "What is the average points of Luka Doncic?",
        "ground_truth": "Luka Doncic has an average of 33.7 points per game."
    },
    {
        "question": "Who has the highest average block?",
        "ground_truth": "victor Wembanyama has the highest average block with 3.0 blocks per game."
    },
    {
        "question": "What is the field goald percentage of Donovan Mitchell?",
        "ground_truth": "Donovan Mitchell has a field goal percentage of 49.2%."
    },
    {
        "question": "Which team has the highest total rebound?",
        "ground_truth": "Haramball has the highest total rebound with 2,371 rebounds."
    },
    {
        "question": "What is Ati and The Hippos's total number of steals?",
        "ground_truth": "Ati and The Hippos have a total of 447 steals."
    }
]
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
questions, answers, contexts, ground_truths, intents = [], [], [], [], []

for item in test_set:
    intent = intent_chain.invoke({"query": item["question"]}).strip().upper()
    
    if "TRADE" in intent:
        current_sys_prompt = trade_prompt_str 
    elif "STATS" in intent:
        current_sys_prompt = stats_prompt_str
    else:
        current_sys_prompt = general_prompt_str

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", current_sys_prompt),
        ("user", "{input}"),
    ])
    qa_chain = create_stuff_documents_chain(llm, qa_prompt)
    temp_rag_chain = create_retrieval_chain(retriever, qa_chain)

    response = temp_rag_chain.invoke({"input": item["question"]})
    

    questions.append(item["question"])
    answers.append(response["answer"])
    contexts.append([doc.page_content for doc in response["context"]])
    ground_truths.append(item["ground_truth"])
    intents.append(intent)

    time.sleep(2) 


dataset = Dataset.from_dict({
    "question": questions,
    "answer": answers,
    "contexts": contexts,
    "ground_truth": ground_truths,
    "intent": intents  
})


print("RAGAS skorları hesaplanıyor")

result = evaluate(
    dataset=dataset,
    metrics=[
        faithfulness,
        context_recall
    ],
    llm=ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        temperature=0
    ),
    embeddings=embeddings
)

print("\n RAGAS Değerlendirme Sonuçları:")
print(result)
