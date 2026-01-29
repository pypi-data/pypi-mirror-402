from setuptools import setup, find_packages

setup(
    name="proprogram",           # NEW unique name
    version="1.0.0",
    author="Divyan S",
    description="Collection of AI/ML programs in Python",
    packages=find_packages(),    # will find your proprogram package
    install_requires=[
        "numpy",
        "tensorflow",
        "matplotlib",
        "scikit-learn",
        "pandas",
        "speechrecognition",
        "pyttsx3"
    ],
    python_requires=">=3.8",
)
