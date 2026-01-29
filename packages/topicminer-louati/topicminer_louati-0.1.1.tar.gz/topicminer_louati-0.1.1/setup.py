import setuptools
import os

# Read the contents of your README file
this_directory = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "TopicMiner - Advanced Topic Modeling Library"

setuptools.setup(
    name="topicminer-louati",
    version="0.1.1",
    author="Louati Mahdi",
    author_email="louatimahdi390@gmail.com",
    description="Advanced topic modeling for Pandas with email auth, metrics, and Plotly visualizations.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/louatimahdi/topicminer",
    packages=setuptools.find_packages(where="."),
    package_dir={"": "."},
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
        "transformers",
        "torch",
        "sentence-transformers"
    ],
)