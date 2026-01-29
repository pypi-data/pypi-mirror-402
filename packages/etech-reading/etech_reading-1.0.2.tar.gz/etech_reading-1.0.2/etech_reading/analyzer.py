# -*- coding: utf-8 -*-
"""
Text Analysis Module for RSVP Display
"""

import re


class TextAnalyzer:
    """Analyzes text for RSVP display"""
    
    @staticmethod
    def split_into_sentences(text):
        """Split text into sentences"""
        sentence_endings = r'[.!?]+(?:\s+|$)'
        sentences = re.split(sentence_endings, text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    @staticmethod
    def get_focus_letter_index(word):
        """
        Get the index of focus letter (OPF - Optimal Position Fixation)
        Fixed position for visual consistency
        """
        if len(word) <= 1:
            return 0, word[0] if word else ''
        elif len(word) <= 2:
            return 0, word[0]
        elif len(word) <= 4:
            return 1, word[1]
        elif len(word) <= 6:
            return 2, word[2]
        elif len(word) <= 8:
            return 3, word[3]
        elif len(word) <= 10:
            return 4, word[4]
        else:
            return len(word) // 2, word[len(word) // 2]
    
    @staticmethod
    def analyze_text(text):
        """Analyze text and prepare it for RSVP display"""
        sentences = TextAnalyzer.split_into_sentences(text)
        result = []
        
        for sent_idx, sentence in enumerate(sentences):
            words = sentence.split()
            word_analysis = []
            
            for word_idx, word in enumerate(words):
                clean_word = re.sub(r'[^\w\u0600-\u06FF]', '', word)
                
                if clean_word:
                    focus_idx, focus_letter = TextAnalyzer.get_focus_letter_index(clean_word)
                    
                    before = clean_word[:focus_idx]
                    after = clean_word[focus_idx + 1:]
                    
                    word_analysis.append({
                        'original': word,
                        'clean': clean_word,
                        'focus_index': focus_idx,
                        'focus_letter': focus_letter,
                        'before': before,
                        'after': after,
                        'word_index': word_idx
                    })
            
            if word_analysis:
                result.append({
                    'sentence_index': sent_idx,
                    'original_sentence': sentence,
                    'words': word_analysis,
                    'word_count': len(word_analysis)
                })
        
        return result
