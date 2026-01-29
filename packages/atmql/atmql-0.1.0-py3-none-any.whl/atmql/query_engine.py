import pandas as pd
from tabulate import tabulate
from .models import TopicModel
from .visualization import Visualizer
from termcolor import colored
import time

class ATMQLEngine:
    def __init__(self, user_info):
        """
        Initialize the query engine

        Parameters:
        - user_info: Dictionary containing user authentication info
        """
        self.user_info = user_info
        self.model = None
        self.visualizer = Visualizer(user_info)
        self.start_time = time.time()

    def load_data(self, texts, model_type="lda", n_topics=5):
        """Load and preprocess data"""
        print(colored("\nLoading and preprocessing data...", "yellow"))
        self.model = TopicModel(texts, model_type=model_type, n_topics=n_topics)
        self.model.train()
        print(colored("Data loaded and model trained successfully!", "green"))

    def execute_query(self, query):
        """Execute a query command"""
        query = query.strip().lower()

        if query.startswith("show topics"):
            n_words = int(query.split("with")[1].strip().split()[0]) if "with" in query else 10
            return self.show_topics(n_words)

        elif query.startswith("show topic distribution"):
            doc_index = int(query.split("for doc")[1].strip())
            return self.show_topic_distribution(doc_index)

        elif query.startswith("show metrics"):
            return self.show_metrics()

        elif query.startswith("show document similarity"):
            parts = query.split()
            doc1 = int(parts[3])
            doc2 = int(parts[5])
            return self.show_document_similarity(doc1, doc2)

        elif query.startswith("show topic similarity"):
            parts = query.split()
            topic1 = int(parts[3])
            topic2 = int(parts[5])
            return self.show_topic_similarity(topic1, topic2)

        elif query.startswith("plot topics"):
            return self.visualizer.plot_topics(self.model)

        elif query.startswith("plot topic distribution"):
            doc_index = int(query.split("for doc")[1].strip())
            return self.visualizer.plot_topic_distribution(self.model, doc_index)

        elif query.startswith("plot coherence"):
            return self.visualizer.plot_coherence(self.model)

        elif query.startswith("plot diversity"):
            return self.visualizer.plot_diversity(self.model)

        elif query.startswith("plot heatmap"):
            return self.visualizer.plot_heatmap(self.model)

        elif query == "help":
            return self.show_help()

        elif query == "exit":
            return "exit"

        else:
            return colored("Invalid query. Type 'help' for available commands.", "red")

    def show_topics(self, n_words=10):
        """Show top words for each topic"""
        topics = self.model.get_topics(n_words)

        if self.model.model_type == "lda":
            table_data = []
            for topic_idx, words in topics:
                table_data.append([f"Topic {topic_idx}", ", ".join(words)])
            return tabulate(table_data, headers=["Topic", "Top Words"], tablefmt="grid")
        else:
            return "\n".join([f"Topic {topic[0]}: {topic[1]}" for topic in topics])

    def show_topic_distribution(self, doc_index):
        """Show topic distribution for a document"""
        dist = self.model.get_topic_distribution(doc_index)
        table_data = [[f"Topic {i}", f"{prob:.4f}"] for i, prob in enumerate(dist)]
        return tabulate(table_data, headers=["Topic", "Probability"], tablefmt="grid")

    def show_metrics(self):
        """Show all topic modeling metrics"""
        coherence = self.model.get_coherence_score()
        diversity = self.model.get_topic_diversity()
        quality = self.model.get_topic_quality()

        metrics = {
            "Coherence Score": coherence,
            "Topic Diversity": diversity,
            "Topic Quality": quality,
            "Number of Topics": self.model.n_topics,
            "Model Type": self.model.model_type.upper()
        }

        table_data = [[k, f"{v:.4f}" if isinstance(v, float) else v] for k, v in metrics.items()]
        return tabulate(table_data, headers=["Metric", "Value"], tablefmt="grid")

    def show_document_similarity(self, doc1, doc2):
        """Show similarity between two documents"""
        similarity = self.model.get_document_similarity(doc1, doc2)
        return f"Similarity between document {doc1} and document {doc2}: {similarity:.4f}"

    def show_topic_similarity(self, topic1, topic2):
        """Show similarity between two topics"""
        similarity = self.model.get_topic_similarity(topic1, topic2)
        return f"Similarity between topic {topic1} and topic {topic2}: {similarity:.4f}"

    def show_help(self):
        """Show available commands"""
        help_text = """
Available ATMQL Commands:

1. Topic Analysis:
   - show topics [with N words] - Show top words for each topic
   - show topic distribution for doc N - Show topic distribution for document N
   - show metrics - Show all topic modeling metrics

2. Similarity Analysis:
   - show document similarity between doc N and doc M - Show similarity between documents
   - show topic similarity between topic N and topic M - Show similarity between topics

3. Visualization:
   - plot topics - Plot topic word distributions
   - plot topic distribution for doc N - Plot topic distribution for document N
   - plot coherence - Plot coherence scores
   - plot diversity - Plot topic diversity
   - plot heatmap - Plot document-topic heatmap

4. Other:
   - help - Show this help message
   - exit - Exit the ATMQL engine
"""
        return help_text

    def get_footer(self):
        """Generate footer with user info and time spent"""
        end_time = time.time()
        time_spent = round(end_time - self.start_time, 2)

        footer = f"""
{colored("="*80, "magenta")}
User Email: {self.user_info['email']}
Sender Email: {self.user_info['sender_email']}
Time Spent: {time_spent} seconds
Auth Time: {self.user_info['auth_time']}

{colored("Thank you for your loyalty and using ATMQL!", "green")}
{colored("Made with ❤️ by Louati Mahdi", "magenta")}
{colored("❤️", "red", attrs=["blink"])}
{colored("="*80, "magenta")}
"""
        return footer