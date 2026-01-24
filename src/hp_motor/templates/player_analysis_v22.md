# HP ENGINE v22.x — BİREYSEL OYUNCU ANALİZ ŞABLONU (KALICI MODÜL)

> Bu dosya HP Engine çekirdek modülüdür. Oyuncu isimlerinden arındırılmıştır. Tüm bireysel analizler bu şablon üzerinden üretilir.

---

## 0. META BİLGİLER

Oyuncu Adı: {{player_name}}

Kulüp: {{club}}

Lig: {{league}}

Sezon: {{season}}

Analizi Yapan: {{analyst}}

Analiz Tarihi: {{analysis_date}}

HP Engine Versiyonu: {{engine_version}}

---

## 1. OYUNCU KİMLİĞİ (PLAYER ID)

Yaş: {{age}}

Boy / Kilo: {{height_weight}}

Dominant Ayak: {{dominant_foot}}

Ana Pozisyon: {{primary_position}}

İkincil Pozisyonlar: {{secondary_positions}}

Kariyer Evresi (Gelişim / Prime / Regresyon): {{career_phase}}

Tek Cümlelik Tanım:

> {{one_liner_definition}}

---

## 2. ROL TANIMI (ROLE DEFINITION)

Birincil Rol: {{primary_role}}

İkincil Rol: {{secondary_role}}

Uygun Olmayan Roller: {{bad_roles}}

Rol Özgürlüğü Seviyesi (Düşük / Orta / Yüksek): {{role_freedom}}

---

## 3. SAYISAL PROFİL (PER 90)

| Metrik | Değer | Lig Yüzdelik |
|---|---:|---:|
| Dripling Başarı % | {{dribble_success}} | {{dribble_pctile}} |
| Top Kaybı | {{turnovers}} | {{turnovers_pctile}} |
| xG | {{xg}} | {{xg_pctile}} |
| xA | {{xa}} | {{xa_pctile}} |
| Kilit Pas | {{key_passes}} | {{key_passes_pctile}} |
| Şut | {{shots}} | {{shots_pctile}} |

Veri Yorumu:

{{numeric_profile_commentary}}

---

## 4. BİYOMEKANİK & BODY LOGIC

Somatotip: {{somatotype}}

Patlayıcılık Seviyesi: {{explosiveness}}

Maksimum Hız: {{max_speed}}

Tekrarlı Sprint Kapasitesi: {{repeated_sprint}}

Fiziksel Dayanım: {{stamina}}

Sakatlık Geçmişi (Varsa): {{injury_history}}

Vücut Oryantasyonu & Alış Açısı Notları:

{{body_orientation_notes}}

---

## 5. OYUN İÇİ KARAR MEKANİZMASI (DECISION TREE)

En Sık Tercih Edilen Aksiyonlar:

{{top_actions}}

Baskı Altında Davranış:

{{under_pressure_behavior}}

---

## 6. TAKTİK ETKİ HARİTASI

En Verimli Alanlar: {{best_zones}}

Etkisiz Alanlar: {{weak_zones}}

Ceza Sahası Katkı Türü: {{box_contribution_type}}

Gol / Asist Üretim Geometrisi:

{{production_geometry}}

---

## 7. PSİKOLOJİK PROFİL

Rol Netliği İhtiyacı: {{role_clarity_need}}

Özgürlük Toleransı: {{freedom_tolerance}}

Hata Sonrası Tepki: {{post_error_response}}

Güven–Performans İlişkisi: {{confidence_performance_relation}}

---

## 8. KULLANIM TALİMATI (COACHING NOTES)

Oyuncu Nasıl Kullanılmalı:

{{how_to_use}}

Oyuncu Nasıl Kullanılmamalı:

{{how_not_to_use}}

Sistem İçi Destek İhtiyaçları:

{{system_support_needs}}

---

## 9. RİSK ANALİZİ

Taktik Riskler: {{tactical_risks}}

Fiziksel Riskler: {{physical_risks}}

Psikolojik Riskler: {{psychological_risks}}

---

## 10. SİSTEM UYUM PUANI

Takım Yapısına Uyum (0–10): {{team_fit_score}}

Lig Uyum Seviyesi (0–10): {{league_fit_score}}

Teknik Direktör Profili Uyumu: {{coach_fit_note}}

---

## 11. NİHAİ HÜKÜM (EXECUTIVE SUMMARY)

> {{executive_summary}}

---

Not: Bu dosya doldurulduktan sonra;

- Scouting Card
- Rol Uyumsuzluğu Alarm Checklist’i
- Takım Etki Simülasyonu modülleri

otomatik olarak türetilir.