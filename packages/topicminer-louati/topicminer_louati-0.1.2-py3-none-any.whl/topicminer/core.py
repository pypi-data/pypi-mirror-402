import pandas as pd
import numpy as np
from tabulate import tabulate
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
import warnings
warnings.filterwarnings("ignore")

class TopicMinerEngine:
    def __init__(self, auth_manager):
        self.auth = auth_manager
        self.topic_model = None
        self.metrics = {}

    def _check_auth(self):
        if not self.auth.token:
            raise PermissionError("Authentication required. Please request a token first.")

    def analyze(self, df, text_column):
        self._check_auth()
        
        if text_column not in df.columns:
            raise ValueError(f"Column '{text_column}' not found in DataFrame.")

        documents = df[text_column].dropna().astype(str).tolist()
        
        vectorizer = CountVectorizer(stop_words="english", min_df=2)
        
        self.topic_model = BERTopic(
            vectorizer_model=vectorizer,
            language="english", 
            calculate_probabilities=True, 
            verbose=True
        )

        topics, probs = self.topic_model.fit_transform(documents)

        freq = self.topic_model.get_topic_freq()
        
        topic_info = {}
        for topic in freq['Topic'].unique():
            if topic != -1:
                keywords = self.topic_model.get_topic(topic)
                topic_info[topic] = [word for word, _ in keywords[:5]]

        unique_topics = freq[freq['Topic'] != -1]['Topic'].tolist()
        self.metrics = {
            'total_topics': len(unique_topics),
            'doc_count': len(documents),
            'outliers': freq[freq['Topic'] == -1]['Count'].sum(),
            'topic_freq': freq[freq['Topic'] != -1],
            'topic_keywords': topic_info
        }

        return self.metrics

    def generate_report(self):
        self._check_auth()
        if not self.metrics:
            raise RuntimeError("No analysis performed yet.")

        table_data = []
        for topic, keywords in self.metrics['topic_keywords'].items():
            count = self.metrics['topic_freq'][self.metrics['topic_freq']['Topic'] == topic]['Count'].values[0]
            table_data.append([topic, count, ", ".join(keywords)])

        headers = ["Topic ID", "Doc Count", "Top Keywords"]
        report = tabulate(table_data, headers=headers, tablefmt="fancy_grid")
        
        summary = (
            f"Total Topics Found: {self.metrics['total_topics']}\n"
            f"Total Documents: {self.metrics['doc_count']}\n"
            f"Outliers Detected: {self.metrics['outliers']}\n"
        )
        
        return f"--- TOPIC MODELING REPORT ---\n\n{summary}\n{report}"

    def get_visualizations(self):
        self._check_auth()
        
        from .visuals import create_topic_distribution_bar, create_word_cloud_mock
        
        figs = {}
        
        if not self.metrics['topic_freq'].empty:
            figs['distribution'] = create_topic_distribution_bar(self.metrics['topic_freq'])
        
        top_words = []
        for topic, words in list(self.metrics['topic_keywords'].items())[:3]:
            for w in words:
                top_words.append((w, 10))
        
        if top_words:
            figs['keywords'] = create_word_cloud_mock(top_words)
            
        return figs