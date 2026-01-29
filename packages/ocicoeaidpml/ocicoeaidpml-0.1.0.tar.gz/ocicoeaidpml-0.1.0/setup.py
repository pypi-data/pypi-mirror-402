from setuptools import setup, find_packages

setup(
    name="coeaidpml",
    version="0.1.0",
    description="Spark schema analysis & ML use-case suggestion tool using OCI LLM",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/coeaidpml",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "pyspark>=3.3.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)