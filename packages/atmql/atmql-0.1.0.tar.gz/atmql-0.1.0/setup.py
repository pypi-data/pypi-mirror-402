from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="atmql",
    version="0.1.0",
    author="Louati Mahdi",
    author_email="louatimahdi390@gmail.com",
    description="Advanced Topic Modeling Query Language with rich terminal visualization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/atmql",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "scikit-learn>=1.0.0",
        "gensim>=4.0.0",
        "tabulate>=0.8.9",
        "matplotlib>=3.4.0",
        "seaborn>=0.11.0",
        "pyfiglet>=0.8.post1",
        "termcolor>=1.1.0",
        "tqdm>=4.62.0",
        "python-dotenv>=0.19.0",
        "smtplib",
        "email",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "atmql=atmql.cli:main",
        ],
    },
)