import pandas as pd

class CognitiveEngine:
    """Proxy for scanning and decision speed using event latency (Jordet Logic)."""
    def analyze_decision_speed(self, df):
        # Time difference between consecutive events for the same player/team
        df['time_delta'] = df['start'].diff().fillna(0)
        # Decision speed is lower time delta in high-pressure zones (x > 66)
        high_pressure = df[df['pos_x'] > 66]
        avg_speed = high_pressure.groupby('code')['time_delta'].mean().sort_values()
        return avg_speed
