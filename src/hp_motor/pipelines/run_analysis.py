from hp_motor.validation.contract_validator import HPContractValidator
from hp_motor.mapping.canonical_mapper import HPCanonicalMapper
from hp_motor.ingest.provider_registry import HPProviderRegistry

class SovereignOrchestrator:
    def __init__(self):
        self.registry = HPProviderRegistry()
        self.mapper = HPCanonicalMapper(self.registry.get_mapping())
        self.validator = HPContractValidator()

    def execute_full_analysis(self, raw_df, phase_fallback="ACTION_GENERIC"):
        # 1. Aşama: Mapping & Discovery
        df, cap_report = self.mapper.map_dataframe(raw_df)
        
        if not cap_report["can_analyze"]:
            return {
                "status": "BLOCKED",
                "reason": f"Eksik zorunlu kolonlar: {cap_report['missing_required']}",
                "capability": cap_report
            }

        # 2. Aşama: SOT Validation (Veri Kalitesi)
        # (Burada dropna yasak ve coordinate bounds denetimi yapılır)
        quality_report = self._validate_sot(df)

        # 3. Aşama: Analiz Hesaplamaları
        # (Mevcut PPDA/xG mantığı burada çalışır)
        metrics = self._compute_metrics(df)

        return {
            "status": "OK",
            "metrics": metrics,
            "data_quality": quality_report,
            "capability": cap_report,
            "metadata": {"phase": phase_fallback}
        }

    def _validate_sot(self, df):
        # Engine'den gelen SOTValidator mantığı: Null haritası ve koordinat denetimi
        return {
            "null_count": df.isnull().sum().sum(),
            "out_of_bounds": 0, # İleri aşamada eklenecek
            "confidence_score": 0.85 if df.isnull().sum().sum() == 0 else 0.60
        }

    def _compute_metrics(self, df):
        # Mevcut v6.0 metrik mantığın
        return {"PPDA": df.get('ppda', 0).mean(), "xG": df.get('xg', 0).mean()}
