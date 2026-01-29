import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from gensim.models import LdaModel
from gensim.corpora import Dictionary
from gensim.models.coherencemodel import CoherenceModel
from tqdm import tqdm
from collections import defaultdict

class TopicModel:
    def __init__(self, texts, model_type="lda", n_topics=5, random_state=42):
        """
        Initialize topic model

        Parameters:
        - texts: List of documents (strings)
        - model_type: "lda" (scikit-learn) or "gensim" (gensim)
        - n_topics: Number of topics to extract
        - random_state: Random seed
        """
        self.texts = texts
        self.model_type = model_type
        self.n_topics = n_topics
        self.random_state = random_state
        self.model = None
        self.vectorizer = None
        self.dictionary = None
        self.corpus = None
        self.topic_term_dists = None
        self.doc_topic_dists = None

    def preprocess(self):
        """Preprocess texts and create required representations"""
        if self.model_type == "lda":
            self.vectorizer = CountVectorizer(max_df=0.95, min_df=2, stop_words="english")
            self.doc_term_matrix = self.vectorizer.fit_transform(self.texts)
        elif self.model_type == "gensim":
            texts = [text.split() for text in self.texts]
            self.dictionary = Dictionary(texts)
            self.corpus = [self.dictionary.doc2bow(text) for text in texts]

    def train(self):
        """Train the topic model"""
        self.preprocess()

        if self.model_type == "lda":
            self.model = LatentDirichletAllocation(
                n_components=self.n_topics,
                random_state=self.random_state,
                learning_method="online"
            )
            self.model.fit(self.doc_term_matrix)
            self.topic_term_dists = self.model.components_ / self.model.components_.sum(axis=1)[:, np.newaxis]
            self.doc_topic_dists = self.model.transform(self.doc_term_matrix)

        elif self.model_type == "gensim":
            self.model = LdaModel(
                corpus=self.corpus,
                id2word=self.dictionary,
                num_topics=self.n_topics,
                random_state=self.random_state,
                passes=10,
                alpha="auto"
            )
            self.topic_term_dists = self.model.get_topics()
            self.doc_topic_dists = np.array([
                [weight for _, weight in self.model.get_document_topics(doc, minimum_probability=0)]
                for doc in self.corpus
            ])

    def get_topics(self, n_words=10):
        """Get top words for each topic"""
        if self.model_type == "lda":
            feature_names = self.vectorizer.get_feature_names_out()
            topics = []
            for topic_idx, topic in enumerate(self.model.components_):
                top_features = [feature_names[i] for i in topic.argsort()[:-n_words - 1:-1]]
                topics.append((topic_idx, top_features))
            return topics
        elif self.model_type == "gensim":
            return self.model.print_topics(num_words=n_words)

    def get_topic_distribution(self, doc_index):
        """Get topic distribution for a specific document"""
        if doc_index >= len(self.doc_topic_dists):
            raise ValueError("Document index out of range")
        return self.doc_topic_dists[doc_index]

    def get_coherence_score(self):
        """Calculate topic coherence score"""
        if self.model_type == "lda":
            texts = [text.split() for text in self.texts]
            cm = CoherenceModel(
                topics=[[self.vectorizer.get_feature_names_out()[i] for i in topic.argsort()[:-11:-1]]
                       for topic in self.model.components_],
                texts=texts,
                dictionary=Dictionary(texts),
                coherence="c_v"
            )
            return cm.get_coherence()
        elif self.model_type == "gensim":
            cm = CoherenceModel(
                model=self.model,
                texts=[text.split() for text in self.texts],
                dictionary=self.dictionary,
                coherence="c_v"
            )
            return cm.get_coherence()

    def get_topic_diversity(self):
        """Calculate topic diversity"""
        if self.topic_term_dists is None:
            return None

        unique_words = set()
        total_words = 0

        for topic in self.topic_term_dists:
            top_words = np.argsort(topic)[-20:]  # Top 20 words per topic
            unique_words.update(top_words)
            total_words += len(top_words)

        return len(unique_words) / total_words

    def get_topic_quality(self):
        """Calculate overall topic quality score"""
        coherence = self.get_coherence_score()
        diversity = self.get_topic_diversity()
        return (coherence + diversity) / 2 if coherence and diversity else None

    def get_document_similarity(self, doc_index1, doc_index2):
        """Calculate similarity between two documents"""
        if doc_index1 >= len(self.doc_topic_dists) or doc_index2 >= len(self.doc_topic_dists):
            raise ValueError("Document index out of range")

        vec1 = self.doc_topic_dists[doc_index1]
        vec2 = self.doc_topic_dists[doc_index2]
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    def get_topic_similarity(self, topic_index1, topic_index2):
        """Calculate similarity between two topics"""
        if topic_index1 >= self.n_topics or topic_index2 >= self.n_topics:
            raise ValueError("Topic index out of range")

        vec1 = self.topic_term_dists[topic_index1]
        vec2 = self.topic_term_dists[topic_index2]
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))