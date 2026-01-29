from .auth import authenticate_user
from .query_engine import ATMQLEngine
from termcolor import colored
import pyfiglet

def main():
    # Authenticate user
    user_info = authenticate_user()
    if not user_info:
        return

    # Initialize query engine
    engine = ATMQLEngine(user_info)

    # Sample data for demonstration
    sample_texts = [
        "Machine learning is a subset of artificial intelligence that focuses on building systems that learn from data.",
        "Deep learning uses neural networks with many layers to model complex patterns in data.",
        "Natural language processing helps computers understand and generate human language.",
        "Computer vision enables machines to interpret and make decisions based on visual input.",
        "Reinforcement learning is about training agents to make sequences of decisions.",
        "Supervised learning uses labeled data to train models for classification and regression tasks.",
        "Unsupervised learning finds patterns in unlabeled data through clustering and association.",
        "Neural networks are computational models inspired by the structure of biological neurons.",
        "Data science combines statistics, programming, and domain knowledge to extract insights from data.",
        "Big data refers to extremely large datasets that require advanced tools to process and analyze."
    ]

    # Load sample data
    engine.load_data(sample_texts, model_type="lda", n_topics=3)

    # Main query loop
    print(colored("\nType 'help' for available commands or 'exit' to quit.\n", "yellow"))

    while True:
        try:
            query = input(colored("ATMQL> ", "cyan")).strip()

            if not query:
                continue

            result = engine.execute_query(query)

            if result == "exit":
                print(engine.get_footer())
                break

            print(result)

        except KeyboardInterrupt:
            print(engine.get_footer())
            break
        except Exception as e:
            print(colored(f"Error: {e}", "red"))

if __name__ == "__main__":
    main()