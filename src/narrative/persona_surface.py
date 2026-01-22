class PersonaPrism:
    """Diyagram v3.0: Aynı gerçeği 4 ayrı karar türüne çeviren prizma."""
    def project_view(self, hypothesis, persona):
        # Ontoloji şemasındaki 'EvidenceNode' ve 'MetricValue' düğümlerini persona bazlı filtreler.
        if persona == "Scout":
            # RoleAssignment & Behavioral Loops odaklı
            return self._extract_role_insights(hypothesis)
        elif persona == "TechnicalDirector":
            # PhaseSegment & Training Triggers odaklı
            return self._extract_tactical_insights(hypothesis)
        # ... diğer personallar
