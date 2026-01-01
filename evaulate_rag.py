import os
import time
from dotenv import load_dotenv
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings

load_dotenv()

# --- 1. SİSTEMİ KUR (app.py'den kopyaladığın kısım) ---
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vector_store = Chroma(persist_directory="nba_fantasy_db", embedding_function=embeddings)
retriever = vector_store.as_retriever(search_kwargs={"k": 20}) # k'yı yüksek tutmak Recall'u artırır

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0) # Hakem model

# RAG Zincirini Oluştur
system_prompt = """
You are an NBA fantasy basketball expert.
Answer the question using ONLY the provided context.
If the answer is not in the context, say "I don't know".
Context:
{context}
"""

prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("user", "{input}")])
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

# --- 2. TEST SETİNİ TANIMLA ---
test_set = [
    {
        "question": "Who is the leading scorer in the league based on AVG_PTS?",
        "ground_truth": "According to the player statistics, Luka Doncic is the leading scorer with an average of 33.7 points per game."
    },
    {
        "question": "Which player has the highest total blocks (TOTAL_BLK) in the dataset?",
        "ground_truth": "Jay Huff has the highest total blocks in the league with 78 blocks."
    },
    {
        "question": "Analyze a trade: I give James Harden and receive Shai Gilgeous-Alexander. Is it a good trade?",
        "ground_truth": "This depends on team needs, but Shai (SGA) generally has higher fantasy value due to better steals and field goal percentage, while Harden offers more assists."
    },
    {
        "question": "Which team has the highest total rebounds according to the league summary?",
        "ground_truth": "The league summary data indicates that the 'Haramball' team has the most total rebounds with 2371."
    },
    {
        "question": "What is the shooting percentage (FG_PCT) of Stephen Curry?",
        "ground_truth": "Stephen Curry has a shooting percentage of approximately 46.5% according to the stats."
    },
    {
        "question": "Compare the efficiency of Nikola Jokic and Giannis Antetokounmpo.",
        "ground_truth": "Nikola Jokic shows higher efficiency in six categories, leading in all except FG%, BLK, and TO."
    },
    {
        "question": "Who is the best free agent available in terms of steals?",
        "ground_truth": "Based on the free agent list in the data, the player Matisse Thybulle with the highest average steals 2.5 per game should be selected." 
    },
    {
        "question": "Does Donovan Mitchell have more than 5 assists per game?",
        "ground_truth": "Yes, Donovan Mitchell averages 5.5 assists per game according to the current statistics."
    },
    {
        "question": "Which team has the worst free throw percentage (FT_PCT)?",
        "ground_truth": "The league data indicates that 'G-Force' has the worst free throw percentage at 74.1%."
    },
    {
        "question": "Is Kadıköy Bulls better than emircanyildirim in the 9 standard categories?",
        "ground_truth": "Kadıköy Bulls is better in assists, steals, blocks, and FT%. However, in a head-to-head matchup, emircanyildirim would win 5-4."
    }
] 

# --- 3. OTOMATİK DOLDURMA DÖNGÜSÜ ---
questions, answers, contexts, ground_truths = [], [], [], []

print("🚀 Bot soruları yanıtlıyor...")
for item in test_set:
    # İşte senin sorduğun yer: app.py'deki zinciri burada çağırıyoruz
    response = rag_chain.invoke({"input": item["question"]})
    
    questions.append(item["question"])
    answers.append(response["answer"])
    # Context'i buradan otomatik çekiyoruz
    contexts.append([doc.page_content for doc in response["context"]])
    ground_truths.append(item["ground_truth"])
    
    time.sleep(2) # Kotaya takılmamak için

# --- 4. RAGAS DEĞERLENDİRME ---
data = {
    "question": questions, "answer": answers, 
    "contexts": contexts, "ground_truth": ground_truths
}
dataset = Dataset.from_dict(data)

print("📊 RAGAS Skorları hesaplanıyor...")
# evaluate fonksiyonunu şu şekilde güncellemek daha güvenli olabilir:
result = evaluate(
    dataset=dataset,
    metrics=[faithfulness, answer_relevancy, context_recall],
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0),
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
)

print("\n🏆 FİNAL RAPORU:")
print(result)