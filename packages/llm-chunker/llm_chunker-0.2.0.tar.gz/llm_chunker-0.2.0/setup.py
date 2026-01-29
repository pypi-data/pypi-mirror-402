from setuptools import setup, find_packages

setup(
    name="llm-chunker",
    version="0.2.0",
    description="A semantic and legal text chunker based on LLM analysis",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Theeojeong",
    author_email="wogusto13@gmail.com",
    url="https://github.com/Theeojeong/llm-chunker",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "openai>=1.0.0",
        "nltk>=3.6",
        "tqdm>=4.0.0",
    ],
    extras_require={
        "fast": [
            "rapidfuzz>=3.0.0",  # 100x faster fuzzy matching
            "json_repair>=0.25.0",  # Robust JSON parsing
        ],
    },
)
