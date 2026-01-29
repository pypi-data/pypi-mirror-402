from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="topicminer-louati",
    version="0.1.0",
    author="Louati Mahdi",
    author_email="louatimahdi390@gmail.com",
    description="An advanced topic modeling library with email authentication, tabulated metrics, and plotly visualizations.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/topicminer", # Update this
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[
        "pandas",
        "numpy",
        "scikit-learn",
        "bertopic",
        "plotly",
        "tabulate",
        "transformers", # Required by BERTopic
        "torch",        # Required by BERTopic
        "sentence-transformers" # Required by BERTopic
    ],
)