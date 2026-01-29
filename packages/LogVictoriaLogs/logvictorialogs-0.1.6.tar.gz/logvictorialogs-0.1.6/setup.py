from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="LogVictoriaLogs",
    version="0.1.6",
    author="Author",
    author_email="author@example.com",
    description="Python client for VictoriaLogs integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/LogVictoriaLogs",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[
        # Add dependencies here
    ],
)
