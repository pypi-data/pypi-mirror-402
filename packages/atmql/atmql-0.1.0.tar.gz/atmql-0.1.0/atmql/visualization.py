import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from termcolor import colored
import os
from datetime import datetime

class Visualizer:
    def __init__(self, user_info):
        """
        Initialize the visualizer

        Parameters:
        - user_info: Dictionary containing user authentication info
        """
        self.user_info = user_info
        self.output_dir = "atmql_plots"
        os.makedirs(self.output_dir, exist_ok=True)

    def _add_footer_to_plot(self, plt):
        """Add footer information to the plot"""
        footer_text = (
            f"User: {self.user_info['email']} | "
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            "Made with ❤️ by Louati Mahdi"
        )
        plt.figtext(0.5, 0.01, footer_text, ha="center", fontsize=8, bbox={"facecolor":"orange", "alpha":0.5, "pad":5})

    def plot_topics(self, model):
        """Plot word distributions for each topic"""
        if model.model_type == "lda":
            feature_names = model.vectorizer.get_feature_names_out()
            fig, axes = plt.subplots(nrows=model.n_topics, figsize=(10, 5*model.n_topics))

            if model.n_topics == 1:
                axes = [axes]

            for topic_idx, ax in enumerate(axes):
                top_features = model.model.components_[topic_idx].argsort()[:-11:-1]
                top_features = [feature_names[i] for i in top_features]
                weights = model.model.components_[topic_idx][top_features]

                ax.barh(top_features, weights, color=sns.color_palette("viridis", len(top_features)))
                ax.set_title(f"Topic {topic_idx}")
                ax.invert_yaxis()

            plt.tight_layout()
            self._add_footer_to_plot(plt)
            plt.savefig(f"{self.output_dir}/topics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            plt.close()
            return colored(f"Topic plots saved to {self.output_dir}/", "green")

        elif model.model_type == "gensim":
            topics = model.model.print_topics(num_words=10)
            for topic in topics:
                print(f"Topic {topic[0]}: {topic[1]}")
            return colored("Gensim LDA topics printed to console.", "green")

    def plot_topic_distribution(self, model, doc_index):
        """Plot topic distribution for a specific document"""
        dist = model.get_topic_distribution(doc_index)

        plt.figure(figsize=(10, 6))
        sns.barplot(x=[f"Topic {i}" for i in range(len(dist))], y=dist, palette="viridis")
        plt.title(f"Topic Distribution for Document {doc_index}")
        plt.ylabel("Probability")
        plt.xticks(rotation=45)
        plt.tight_layout()
        self._add_footer_to_plot(plt)
        plt.savefig(f"{self.output_dir}/topic_dist_doc{doc_index}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.close()
        return colored(f"Topic distribution plot saved to {self.output_dir}/", "green")

    def plot_coherence(self, model):
        """Plot coherence scores"""
        coherence = model.get_coherence_score()

        plt.figure(figsize=(8, 5))
        sns.barplot(x=["Coherence Score"], y=[coherence], palette="viridis")
        plt.title("Topic Coherence Score")
        plt.ylabel("Score")
        plt.ylim(0, 1)
        plt.tight_layout()
        self._add_footer_to_plot(plt)
        plt.savefig(f"{self.output_dir}/coherence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.close()
        return colored(f"Coherence plot saved to {self.output_dir}/", "green")

    def plot_diversity(self, model):
        """Plot topic diversity"""
        diversity = model.get_topic_diversity()

        plt.figure(figsize=(8, 5))
        sns.barplot(x=["Topic Diversity"], y=[diversity], palette="viridis")
        plt.title("Topic Diversity")
        plt.ylabel("Score")
        plt.ylim(0, 1)
        plt.tight_layout()
        self._add_footer_to_plot(plt)
        plt.savefig(f"{self.output_dir}/diversity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.close()
        return colored(f"Diversity plot saved to {self.output_dir}/", "green")

    def plot_heatmap(self, model):
        """Plot document-topic heatmap"""
        if model.doc_topic_dists is None:
            return colored("No document-topic distributions available.", "red")

        plt.figure(figsize=(12, 8))
        sns.heatmap(model.doc_topic_dists, cmap="viridis", xticklabels=[f"Topic {i}" for i in range(model.n_topics)])
        plt.title("Document-Topic Heatmap")
        plt.xlabel("Topics")
        plt.ylabel("Documents")
        plt.tight_layout()
        self._add_footer_to_plot(plt)
        plt.savefig(f"{self.output_dir}/heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.close()
        return colored(f"Heatmap saved to {self.output_dir}/", "green")