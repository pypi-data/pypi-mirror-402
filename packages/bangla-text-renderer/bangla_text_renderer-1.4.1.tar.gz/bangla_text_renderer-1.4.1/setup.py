from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bangla-text-renderer",
    version="1.4.1",
    author="Mahfazzalin Shawon Reza",
    author_email="mahfazzalin1@gmail.com",
    description="Perfect Bangla/Bengali text rendering on images/video with correct vowel positioning and joint letter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Mahfazzalin/bangla-text-renderer",  # GitHub repo
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.7",
    install_requires=[
        "Pillow>=8.0.0",
    ],
    keywords="bangla bengali text rendering image video vowel positioning perfect joint letter unicode typography",
)