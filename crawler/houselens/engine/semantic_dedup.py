from typing import List, Tuple, Optional
from houselens.models.property import StandardProperty
import logging

class RuleBasedScorer:
    """
    Score-based semantic deduplication engine.
    Does NOT consider price, as pricing strategies vary across brokers.
    """
    @staticmethod
    def evaluate(new_property: StandardProperty, candidates: List[StandardProperty]) -> Tuple[Optional[StandardProperty], int]:
        """
        Evaluates a list of candidates against the new_property.
        Returns the best matched property and its score.
        """
        best_match = None
        highest_score = 0
        
        for candidate in candidates:
            score = RuleBasedScorer.calculate_score(new_property, candidate)
            if score > highest_score:
                highest_score = score
                best_match = candidate
                
        return best_match, highest_score

    @staticmethod
    def calculate_score(prop1: StandardProperty, prop2: StandardProperty) -> int:
        score = 0
        
        # 1. Source ID / URL Check (Source Platform Deduplication)
        # If they are from the same platform and have the same source_id or URL, they are absolutely the same
        if prop1.source_platform == prop2.source_platform:
            if prop1.source_id == prop2.source_id:
                return 100
            if prop1.url and prop2.url and prop1.url == prop2.url:
                return 100
        
        # 2. Address Matching (Very High Weight: 40 points)
        # At this point, we know city, district, street match (from SQL filter).
        # We need to compare the raw address to see if the door number matches.
        # This is a naive exact string match for the MVP. More advanced parsing could extract exact numbers.
        if prop1.address and prop2.address:
            # Strip common suffixes and spaces
            a1 = prop1.address.replace(' ', '').replace('號', '')
            a2 = prop2.address.replace(' ', '').replace('號', '')
            if a1 == a2:
                score += 40
            else:
                # If the strings don't exactly match but they are on the same street, it might still be the same, 
                # but we give fewer or zero points.
                pass

        # 3. Floor Matching (High Weight: 25 points)
        # Allow exact match or a slight discrepancy (e.g. 5F vs 6F, or one hides the exact floor)
        f1 = prop1.floor.replace('F', '').replace('樓', '').strip()
        f2 = prop2.floor.replace('F', '').replace('樓', '').strip()
        if f1 and f2 and f1 == f2:
            score += 25
        elif f1 and f2:
            try:
                # If they are numbers, allow +/- 1 floor difference due to typos or broker obfuscation
                if abs(int(f1) - int(f2)) <= 1:
                    score += 15
            except ValueError:
                pass

        # 4. Ping Matching (Extremely High Weight: 35 points)
        # Ping is statutory data. It rarely varies significantly.
        # Use main_building_ping if both have it, otherwise fallback to building_ping (total).
        p1 = prop1.main_building_ping if (prop1.main_building_ping and prop1.main_building_ping > 0) else prop1.building_ping
        p2 = prop2.main_building_ping if (prop2.main_building_ping and prop2.main_building_ping > 0) else prop2.building_ping
        
        if p1 > 0 and p2 > 0:
            diff_ratio = abs(p1 - p2) / p1
            if diff_ratio <= 0.01: # 1% error
                score += 35
            elif diff_ratio <= 0.02: # 2% error
                score += 20
                
        # 5. Layout Matching (Medium Weight: 10 points)
        if prop1.rooms == prop2.rooms and prop1.bathrooms == prop2.bathrooms and prop1.rooms > 0:
            score += 10

        return score
