# 🏀 NBA Fantasy Chatbot

## Projenin Tanımı ve Amacı
Bu proje, NBA Fantasy Basketball oyuncularının veri odaklı kararlar almasını sağlamak amacıyla geliştirilmiş, **Retrieval-Augmented Generation (RAG)** mimarisine sahip yapay zeka tabanlı bir asistandır.

Bu sistem, sadece genel NBA bilgisiyle değil, **Yahoo Fantasy API** üzerinden çekilen gerçek zamanlı ve spesifik lig verileriyle (AVG/TOTAL istatistikler, takım sahiplikleri, pozisyon bilgileri) ile beslenmektedir. 

### Temel Hedefler:
**1-Veri Odaklı Strateji:** Kullanıcıların "Kim daha iyi skorer?" veya "Bu takas mantıklı mı?" gibi sorularına, sadece LLM'in eğitimiyle değil, güncel lig veritabanıyla (ChromaDB) tutarlı yanıtlar vermek.

**2-Niyet Sınıflandırma (Intent Classification):** Kullanıcı sorularını analiz ederek; istatistik sorguları, takas analizleri veya selamlama niyetlerini birbirinden ayırıp her biri için optimize edilmiş cevapları sunmak.

**3-Halüsinasyonu Engellemek:** RAG mimarisi sayesinde, modelin veri setinde bulunmayan bilgileri "uydurmasının" önüne geçerek sadece mevcut JSON verilerine sadık kalmasını sağlamak.

## Gereksinimler
* [VS Code](https://code.visualstudio.com/)
* [Anaconda](https://www.anaconda.com/download) veya [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
* [Yahoo Developer Hesabı](https://developer.yahoo.com/fantasysports/guide/) Yahoo Fantasy API erişimi için
* [Yahoo Fantasy Hesabı](https://sports.yahoo.com) Verilerin çekileceği aktif bir NBA ligi üyeliği.

## Kurulum

Projeyi yerel ortamınızda ayağa kaldırmak için aşağıdaki adımları takip edin:

### 1. Terminali açın ve repoyu klonlayın:
```bash
git clone https://github.com/kaannerenn/nba-fantasy-chatbot.git [directory name]
```
### 2.Proje dizinine ilerleyin:
```bash
cd [directory name]/nba-fantasy-chatbot
```
### 3.Conda ortamı oluşturun
```bash
conda create -n [environment name] python=3.10
conda activate [environment name]
```
### 4.Gerekli kütüphaneleri yükleyin
```bash
pip install -r requirements.txt
```

## Kullanım
### 1. .env dosyasınızı kendi bilgileriniz özelinde doldurun.

### 2. Yahoo Fantasy API üzerinden liginizdeki verileri çekin.
```bash
python recieving_data_from_yahoo/recieve_players_data.py
```
```bash
python recieving_data_from_yahoo/recieve_teams_data.py
```

### 3. Haftalık verileri total ve average olarak dönüştürün.
```bash
python convert_to_avg_total.py
```

### 4. Uygulamayı çalıştırın.
```bash
streamlit run app.py
```
