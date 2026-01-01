# 🏀 NBA Fantasy Chatbot

## Projenin Tanımı ve Amacı
Bu proje, NBA Fantasy Basketball oyuncularının veri odaklı kararlar almasını sağlamak amacıyla geliştirilmiş, **Retrieval-Augmented Generation (RAG)** mimarisine sahip yapay zeka tabanlı bir asistandır.

Bu sistem, sadece genel NBA bilgisiyle değil, **Yahoo Fantasy API** üzerinden çekilen gerçek zamanlı ve spesifik lig verileriyle (AVG/TOTAL istatistikler, takım sahiplikleri, pozisyon bilgileri) ile beslenmektedir. 

### Temel Hedefler:
**1-Veri Odaklı Strateji:** Kullanıcıların "Kim daha iyi skorer?" veya "Bu takas mantıklı mı?" gibi sorularına, sadece LLM'in eğitimiyle değil, güncel lig veritabanıyla (ChromaDB) tutarlı yanıtlar vermek.
**2-Niyet Sınıflandırma (Intent Classification):** Kullanıcı sorularını analiz ederek; istatistik sorguları, takas analizleri veya selamlama niyetlerini birbirinden ayırıp her biri için optimize edilmiş cevapları sunmak.
**3-Halüsinasyonu Engellemek:** RAG mimarisi sayesinde, modelin veri setinde bulunmayan bilgileri "uydurmasının" önüne geçerek sadece mevcut JSON verilerine sadık kalmasını sağlamak.