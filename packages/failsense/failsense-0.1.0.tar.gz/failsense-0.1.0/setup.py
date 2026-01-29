from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="failsense",
    version="0.1.0",
    author="FailSense Team",
    author_email="support@failsense.com",
    description="Error tracking and LLM monitoring for Python applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/failsense/failsense-python",
    project_urls={
        "Bug Tracker": "https://github.com/failsense/failsense-python/issues",
        "Documentation": "https://docs.failsense.com",
        "Homepage": "https://failsense.com",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0,<3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "mypy>=0.950",
        ],
    },
    keywords="error-tracking monitoring llm ai observability failsense",
)
