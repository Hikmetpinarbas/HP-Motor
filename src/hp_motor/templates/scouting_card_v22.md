# HP ENGINE v22.x — SCOUTING CARD (TEK SAYFA) — ŞABLON

Bu çıktı, Bireysel Oyuncu Analiz Şablonundan türetilen tek sayfalık karar kartıdır.

---

OYUNCU: {{player_name}}
KULÜP / LİG / SEZON: {{club_league_season}}
POZİSYON / ROL: {{position_role}}
DOMINANT AYAK: {{dominant_foot}}
YAŞ / BOY / KİLO: {{age_height_weight}}

---

## 1) TEK CÜMLELİK HÜKÜM

> {{one_sentence_verdict}}

---

## 2) SAYISAL ÇEKİRDEK (PER 90)

| xG | xA | Kilit Pas | Şut | Dripling % | Top Kaybı |
|---:|---:|---:|---:|---:|---:|
| {{xg}} | {{xa}} | {{key_passes}} | {{shots}} | {{dribble_success}} | {{turnovers}} |

---

## 3) PROFİL ETİKETLERİ (KISA)

Arketip: {{archetype}}

En Verimli Bölge: {{best_zone}}

Ana Silah (1–2): {{main_weapons}}

Limit (1–2): {{main_limits}}

---

## 4) KULLANIM TALİMATI (3 MADDE)

1. {{usage_1}}
2. {{usage_2}}
3. {{usage_3}}

---

## 5) KOŞUL BAĞIMLILIKLARI (EVET/HAYIR)

Overlap / Bindirme desteği gerekir mi? {{need_overlap}}

Duvar (10/8) istasyonu gerekir mi? {{need_wall_station}}

9 numara sabitlemesi kritik mi? {{need_9_anchor}}

Ters kanat arka direk koşusu ister mi? {{need_far_post_runner}}

---

## 6) RİSKLER (KIRMIZI BAYRAK)

Taktik: {{risk_tactical}}

Fiziksel: {{risk_physical}}

Psikolojik: {{risk_psychological}}

---

## 7) UYUM SKORU (0–10)

Takım Yapısı Uyum: {{fit_team}}

Lig Uyum: {{fit_league}}

TD Profil Uyum: {{fit_coach}}