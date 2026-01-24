# HP ENGINE v22.x — ROL UYUMSUZLUĞU ALARM CHECKLIST’İ (RISK SKORU)

> Bu modül, Bireysel Oyuncu Analiz Şablonundan türetilir. Amaç: Oyuncunun sahaya “yanlış rol/yanlış bağlam” ile sürülmesi halinde performans düşüşünü önceden yakalamak ve antrenör/analist için net aksiyon üretmektir.

---

## 0) KULLANIM PROTOKOLÜ

Bu checklist maç planı, rol tarif toplantısı ve ilk 3 hafta adaptasyon döneminde zorunlu çalıştırılır.

Sonuç üç seviyeye ayrılır: **Yeşil (0–3)** / **Sarı (4–7)** / **Kırmızı (8+)**

Kırmızı seviyede: rol revizyonu veya destek eklemesi yapılmadan “oyuncu değerlendirmesi” geçersiz sayılır.

---

## 1) CHECKLIST — EVET/HAYIR + PUAN

### A) ROL TARİFİ UYUMU

1. Oyuncunun birincil rolü saha planında net mi?  
   **{{q1_answer}}** ({{q1_points}})

2. Oyuncu çizgiye hapsediliyor mu? (line-hugging zorunluluğu)  
   **{{q2_answer}}** ({{q2_points}})

3. Oyuncu “tek başına çöz” moduna itilmiş mi? (izole 1v2–1v3)  
   **{{q3_answer}}** ({{q3_points}})

4. Oyuncunun top aldığı bölgeler, en verimli bölgeyle örtüşüyor mu?  
   **{{q4_answer}}** ({{q4_points}})

### B) DESTEK VE BAĞLANTILAR (LINK-UP)

5. Aynı koridorda duvar/istasyon var mı? (10/8, iç oyuncu)  
   **{{q5_answer}}** ({{q5_points}})

6. Overlap/underlap desteği planlı mı? (bek/kanat arası)  
   **{{q6_answer}}** ({{q6_points}})

7. 9 numara stoperleri sabitliyor mu? (pinning)  
   **{{q7_answer}}** ({{q7_points}})

8. Ters kanat arka direk koşusu var mı? (space-occupancy)  
   **{{q8_answer}}** ({{q8_points}})

### C) OYUN AKIŞI VE TOPA DOKUNUŞ PROBLEMİ

9. İlk 20 dakikada oyuncu hedefli 3+ temas aldı mı?  
   **{{q9_answer}}** ({{q9_points}})

10. Oyuncu topu sürekli kapalı vücutla mı alıyor?  
    **{{q10_answer}}** ({{q10_points}})

11. Topu aldığı anlarda “ikinci opsiyon” var mı? (pas çıkışı)  
    **{{q11_answer}}** ({{q11_points}})

### D) RİSK YÖNETİMİ (FİZİKSEL + PSİKOLOJİK)

12. Oyuncunun yük yönetimi planlı mı? (haftalık dakika/yoğunluk)  
    **{{q12_answer}}** ({{q12_points}})

13. Fiziksel temas yoğunluğu oyuncu profiline göre ayarlanmış mı?  
    **{{q13_answer}}** ({{q13_points}})

14. Rol iletişimi ve güven çerçevesi kurulmuş mu? (net rol, net beklenti)  
    **{{q14_answer}}** ({{q14_points}})

---

## TOPLAM RİSK SKORU

**{{total_score}} / 14**  
**Seviye:** **{{band}}**

---

## 2) SEVİYE OKUMASI (SCORE INTERPRETATION)

- **0–3 | YEŞİL:** Rol doğru. Performans yorumu geçerli.
- **4–7 | SARI:** Performans dalgalanması beklenir. 1–2 destek/rol düzeltmesi şart.
- **8+ | KIRMIZI:** “Yanlış bağlam” alarmı. Rol revizyonu olmadan oyuncu hükmü verilmez.

---

## 3) TETİKLEYİCİ GÖSTERGELER (CANLI MAÇ İÇİ)

Aşağıdaki tetikleyicilerden 2’si görülürse alarm seviyesi bir kademe yükseltilir:

{{live_triggers_block}}

---

## 4) AKSİYON MATRİSİ (NE YAPMALI?)

### YEŞİL AKSİYON
{{green_actions_block}}

### SARI AKSİYON (EN HIZLI 3 DÜZELTME)
{{yellow_actions_block}}

### KIRMIZI AKSİYON (ROL REVİZYONU)
{{red_actions_block}}

---

## 5) HÜKÜM (BAĞLAM DOĞRULAMA)

> {{judgement_line}}

---

## 6) MODÜL NOTLARI (HP ENGINE)

Bu checklist, oyuncu performansını “bireysel kalite” ile karıştırmayı engeller.  
Amaç: Hüküm vermek değil, hükmün geçerli olacağı bağlamı doğrulamak.