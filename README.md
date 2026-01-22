# HP Motor v3.0 | Sovereign Intelligence

Futbol analizinde "Sıfır Hata" ve "Maksimum Şeffaflık" prensibiyle kurgulanmış otonom bir analiz motorudur.

## 🛡️ Anayasa Kuralları
1. **Veri Muhafazası:** Hiçbir veri sessizce silinmez (`dropna` yasaktır). Koordinat sistemindeki 0.0 değerleri meşru kabul edilir.
2. **Canonical Transform:** Tüm veriler $105 \times 68$ metre bazlı standart düzleme normalize edilir.
3. **Registry-Driven:** Analiz mantığı kodun içinde değil, YAML tabanlı Registry dosyalarında yaşar.

## 🚀 Kurulum
1. `pip install -r requirements.txt`
2. `streamlit run streamlit_app.py`
