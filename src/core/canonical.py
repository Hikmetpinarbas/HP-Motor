# src/core/canonical.py
class CanonicalAction:
    """HP-CDL: Her türlü verinin (Event/Text/Video) ortak dili."""
    def __init__(self, source_id, timestamp, player_id, action_type, confidence):
        self.id = source_id
        self.time = timestamp
        self.player = player_id
        self.type = action_type  # 'pass', 'tactical_note', 'video_tag'
        self.confidence = confidence
