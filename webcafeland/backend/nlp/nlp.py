import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.ensemble import RandomForestClassifier
import re
import string
import pickle
import os

class WordFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract features from each word for classification"""
    
    def __init__(self):
        pass
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        features = []
        
        for word in X:
            word = str(word).lower()
            
            # Extract various features that might be predictive of word level
            features.append({
                'length': len(word),
                'syllables': self._count_syllables(word),
                'has_prefix': int(self._has_prefix(word)),
                'has_suffix': int(self._has_suffix(word)),
                'contains_hyphen': int('-' in word),
                'contains_uncommon_char': int(bool(re.search('[jqxzv]', word.lower()))),
                'vowel_consonant_ratio': self._vowel_consonant_ratio(word),
                'capital_letters': sum(1 for c in word if c.isupper()),
                'hard_consonants': len(re.findall(r'[bcdgkpqt]', word.lower())),
                'word_pattern_complexity': len(set(word)) / len(word) if len(word) > 0 else 0,
            })
        
        return pd.DataFrame(features)
    
    def _count_syllables(self, word):
        """Rough estimation of syllables"""
        word = word.lower()
        word = re.sub(r'[^a-zA-Z]', '', word)
        count = 0
        vowels = "aeiouy"
        
        if len(word) == 0:
            return 0
        
        # Count consecutive vowels as one syllable
        prev_is_vowel = False
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_is_vowel:
                count += 1
            prev_is_vowel = is_vowel
        
        # Handle trailing e
        if word.endswith('e'):
            count -= 1
            
        # Ensure at least one syllable
        return max(1, count)
    
    def _has_prefix(self, word):
        common_prefixes = ['un', 're', 'in', 'im', 'dis', 'en', 'em', 'non', 'pre', 'pro', 'anti']
        return any(word.lower().startswith(prefix) for prefix in common_prefixes)
    
    def _has_suffix(self, word):
        common_suffixes = ['ing', 'ed', 'ly', 'tion', 'ment', 'ness', 'ity', 'ize', 'able', 'ible', 'ful', 'less']
        return any(word.lower().endswith(suffix) for suffix in common_suffixes)
    
    def _vowel_consonant_ratio(self, word):
        if not word:
            return 0
        vowels = sum(1 for char in word.lower() if char in 'aeiou')
        consonants = sum(1 for char in word.lower() if char in 'bcdfghjklmnpqrstvwxyz')
        return vowels / max(consonants, 1)  # Avoid division by zero

class VocabularyLevelClassifier:
    """Classify words into Preschool, Elementary, or Middle school level"""
    
    def __init__(self):
        self.model = Pipeline([
            ('features', WordFeatureExtractor()),
            ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
        ])
        self.level_mapping = {
            'Preschool': 0,
            'Elementary': 1,
            'Middle': 2
        }
        self.reverse_mapping = {v: k for k, v in self.level_mapping.items()}
        
    def train(self, data_path):
        """Train the model with vocabulary data"""
        # Load data
        df = pd.read_csv(data_path)
        
        # Remove duplicates and shuffle
        df = df.drop_duplicates(subset=['Word'])
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        # Split data
        X = df['Word']
        y = df['Level'].map(self.level_mapping)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Model accuracy: {accuracy:.4f}")
        
        # Detailed evaluation
        print("\nClassification Report:")
        print(classification_report(
            y_test, 
            y_pred, 
            target_names=self.level_mapping.keys()
        ))
        
        # Confusion Matrix
        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        
        return accuracy
    
    def predict(self, words):
        """Predict the vocabulary level for a list of words"""
        if isinstance(words, str):
            words = [words]
            
        predictions = self.model.predict(words)
        return [self.reverse_mapping[pred] for pred in predictions]
    
    def predict_with_probabilities(self, words):
        """Predict with probabilities for each class"""
        if isinstance(words, str):
            words = [words]
            
        predictions = self.model.predict(words)
        probabilities = self.model.predict_proba(words)
        
        results = []
        for i, word in enumerate(words):
            pred_class = self.reverse_mapping[predictions[i]]
            probs = {self.reverse_mapping[j]: prob for j, prob in enumerate(probabilities[i])}
            results.append({
                'word': word,
                'predicted_level': pred_class,
                'probabilities': probs
            })
            
        return results
    
    def save(self, path='vocab_level_model.pkl'):
        """Save the trained model to disk"""
        with open(path, 'wb') as f:
            pickle.dump(self, f)
        print(f"Model saved to {path}")
    
    @classmethod
    def load(cls, path='vocab_level_model.pkl'):
        """Load a trained model from disk"""
        with open(path, 'rb') as f:
            model = pickle.load(f)
        print(f"Model loaded from {path}")
        return model

if __name__ == "__main__":
    # Path to your dataset
    data_path = "/Users/gk/webcafeland/backend/nlp/Vocabulary_Level_Classification_Dataset.csv"
    
    # Create and train the classifier
    classifier = VocabularyLevelClassifier()
    classifier.train(data_path)
    
    # Save the model
    classifier.save("/Users/gk/webcafeland/backend/nlp/vocab_level_model.pkl")
    
    # Example usage
    test_words = ["happy", "algorithm", "dinosaur", "apple", "hypothesis", "ball"]
    predictions = classifier.predict(test_words)
    
    print("\nExample predictions:")
    for word, pred in zip(test_words, predictions):
        print(f"{word}: {pred}")
        
    # Get detailed predictions with probabilities
    detailed_results = classifier.predict_with_probabilities(test_words)
    print("\nDetailed predictions:")
    for result in detailed_results:
        print(f"\n{result['word']}: {result['predicted_level']}")
        print("Probabilities:")
        for level, prob in result['probabilities'].items():
            print(f"  {level}: {prob:.4f}")