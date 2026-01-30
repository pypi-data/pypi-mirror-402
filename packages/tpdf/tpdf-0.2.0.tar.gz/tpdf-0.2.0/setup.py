from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tpdf",
    version="0.2.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Text Portable Document Format - AI-friendly PDF generation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/thecoolrobot/tpdf",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Printing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "reportlab>=4.0.0",
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": ["pytest>=7.0", "black>=22.0", "flake8>=4.0"],
    },
)