# Aerospace Compliance Platform

MIL-STD-810H, DO-178C gibi havacılık ve savunma standartlarıyla
teknik raporların uyumluluğunu otomatik analiz eden yapay zeka platformu.

## Özellikler
- PDF standartlarını vektör veritabanına (ChromaDB) indeksleme
- RAG ile anlamsal arama ve uyumluluk analizi
- Clean Architecture + Repository Pattern
- FastAPI REST API
- SQLite veritabanı (ORM ile, ham SQL yok)
- 25 unit test

## Kurulum

### 1. Gereksinimler
- Python 3.10+
- Git

### 2. Projeyi Kur
```bash
git clone <repo-url>
cd aerospace_compliance
python -m venv venv --system-site-packages
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Ortam Değişkenlerini Ayarla
`.env` dosyasını oluştur:
```
OPENAI_API_KEY="your-key-here"
```

### 4. Çalıştır
```bash
python -m uvicorn main:app --reload
```

### 5. API Dokümantasyonu
```
http://127.0.0.1:8000/docs
```

## Testleri Çalıştır
```bash
python -m pytest tests/ -v
```

## Proje Yapısı
```
aerospace_compliance/
├── src/
│   ├── domain/          # Entity'ler ve Interface'ler
│   ├── infrastructure/  # ORM, Repository implementasyonları
│   ├── application/     # İş mantığı servisleri
│   ├── api/             # FastAPI route'ları
│   └── rag/             # PDF okuma, chunking, ChromaDB
├── tests/               # Unit testler
├── uploads/             # Yüklenen PDF'ler
└── main.py              # Uygulama giriş noktası
```

## Kullanılan Standartlar
- MIL-STD-810H (Çevresel Mühendislik)
- MIL-STD-461G (Elektromanyetik Uyumluluk)
- DO-178C (Yazılım Sertifikasyonu)

## Mimari
Clean Architecture + N-Tier:
- **Domain**: Saf Python, sıfır dış bağımlılık
- **Infrastructure**: SQLAlchemy ORM, ChromaDB
- **Application**: İş mantığı servisleri
- **API**: FastAPI endpoint'leri