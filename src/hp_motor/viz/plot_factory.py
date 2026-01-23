import matplotlib.pyplot as plt
from mplsoccer import Pitch
import seaborn as sns

class HPPlotFactory:
    """HP Motor v5.0 - Tenebrism/Tesla Estetiğiyle Görsel Analiz"""
    
    def __init__(self):
        self.bg_color = '#000000'
        self.line_color = '#FFD700' # Altın Sinyal

    def plot_trauma_zones(self, trauma_df):
        """Sapolsky/Mate: Hataların yoğunlaştığı travma bölgelerini çizer."""
        pitch = Pitch(pitch_type='custom', pitch_length=105, pitch_width=68,
                      pitch_color=self.bg_color, line_color=self.line_color)
        fig, ax = pitch.draw(figsize=(10, 7))
        
        if not trauma_df.empty:
            sns.kdeplot(x=trauma_df['pos_x'], y=trauma_df['pos_y'], 
                        ax=ax, fill=True, cmap='YlOrBr', alpha=0.5, levels=10)
            pitch.scatter(trauma_df['pos_x'], trauma_df['pos_y'], 
                          ax=ax, color='red', s=60, edgecolors='white', label='Trauma')
            
        plt.title("Spatial Trauma Analysis (Sapolsky Loop)", color=self.line_color, family='monospace', size=15)
        return fig
