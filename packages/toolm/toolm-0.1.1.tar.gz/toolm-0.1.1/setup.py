from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="toolm",
    version="0.1.1",
    author="Louati Mahdi",
    author_email="louatimahdi390@gmail.com",
    description="A lightweight framework for building AI Agents using Google Gemini API.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mahdi123-tech",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires='>=3.9',
    install_requires=[
        "google-generativeai>=0.7.0",
    ],
    keywords=["gemini", "ai", "agent", "llm", "framework", "google"],
)