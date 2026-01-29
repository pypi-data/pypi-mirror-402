from setuptools import setup, find_packages

setup(
    name="Topsis_Sanyam_102303059",
    version="1.0.1",
    author="Sanyam Wadhwa",
    author_email="sanyamwadhwa.in@gmail.com",
    description="A Python package for TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution) analysis.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/SanyamWadhwa07/topsis_Sanyam_102303059",
    packages=find_packages(),
    install_requires=["numpy", "pandas"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)