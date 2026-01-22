from engine.validator import SOTValidator

class MasterOrchestrator:
    def __init__(self):
        self.validator = SOTValidator()

    def run_pipeline(self, raw_df):
        # ADIM 1: SOT Gate (Veri Denetimi)
        report, validated_data = self.validator.validate(raw_df)
        
        if report['status'] == "BLOCKED":
            return {"success": False, "report": report}

        # ADIM 2: Analitik Çıktı (Şimdilik İskelet)
        results = {
            "engine": "HP-Motor v3.0",
            "audit_note": "Veri anayasal süzgeçten geçti. 0.0 değerleri korundu.",
            "verified_metrics": []
        }

        return {
            "success": True,
            "report": report,
            "data": validated_data,
            "results": results
        }
