import re
import math
from typing import Dict, Any

class VisualEngine:
    """WCAG 2.1 relative luminance math, contrast calculator, alt-text quality, and readability formulas."""

    @staticmethod
    def _luminance(r: int, g: int, b: int) -> float:
        values = []
        for c in (r, g, b):
            v = c / 255.0
            if v <= 0.03928:
                values.append(v / 12.92)
            else:
                values.append(math.pow((v + 0.055) / 1.055, 2.4))
        return values[0] * 0.2126 + values[1] * 0.7152 + values[2] * 0.0722

    @staticmethod
    def _hex_to_rgb(hex_str: str) -> tuple:
        clean_hex = hex_str.lstrip('#')
        if len(clean_hex) == 3:
            clean_hex = ''.join(c * 2 for c in clean_hex)
        rgb = tuple(int(clean_hex[i:i+2], 16) for i in (0, 2, 4))
        return rgb

    def calculate_contrast(self, fg_hex: str, bg_hex: str) -> Dict[str, Any]:
        try:
            fg_rgb = self._hex_to_rgb(fg_hex)
            bg_rgb = self._hex_to_rgb(bg_hex)
            lum1 = self._luminance(*fg_rgb)
            lum2 = self._luminance(*bg_rgb)
            brightest = max(lum1, lum2)
            darkest = min(lum1, lum2)
            ratio = round((brightest + 0.05) / (darkest + 0.05), 2)
            return {
                "ratio": ratio,
                "passesAANormalText": ratio >= 4.5,
                "passesAALargeText": ratio >= 3.0,
                "passesAAA": ratio >= 7.0
            }
        except Exception:
            return {
                "ratio": 1.0,
                "passesAANormalText": False,
                "passesAALargeText": False,
                "passesAAA": False
            }

    def calculate_readability(self, text: str) -> Dict[str, Any]:
        """Calculates Flesch Reading Ease and Flesch-Kincaid Grade Level."""
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]

        total_words = max(1, len(words))
        total_sentences = max(1, len(sentences))

        # Estimate syllables
        def count_syllables(w):
            w = w.lower()
            count = len(re.findall(r'[aeiouy]+', w))
            if w.endswith('e') and not w.endswith('le') and len(w) > 2:
                count = max(1, count - 1)
            return max(1, count)

        total_syllables = sum(count_syllables(w) for w in words)

        # Flesch Reading Ease = 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
        ease = 206.835 - (1.015 * (total_words / total_sentences)) - (84.6 * (total_syllables / total_words))
        ease = max(0.0, min(100.0, round(ease, 1)))

        # Flesch-Kincaid Grade Level = 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
        grade = (0.39 * (total_words / total_sentences)) + (11.8 * (total_syllables / total_words)) - 15.59
        grade = max(1.0, round(grade, 1))

        if ease >= 70:
            label = "Easy / Conversational"
        elif ease >= 60:
            label = "Standard Plain English"
        elif ease >= 50:
            label = "Fairly Difficult / Technical"
        else:
            label = "Difficult / Academic"

        return {
            "readingEase": ease,
            "gradeLevel": grade,
            "readingLevelLabel": label,
            "sentenceCount": total_sentences,
            "wordCount": total_words
        }

visual_engine = VisualEngine()
