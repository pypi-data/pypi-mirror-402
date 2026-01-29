from setuptools import setup, find_packages

setup(
    name="Topsis-Tanya-102303077",
    version="1.0.3",
    author="Tanya Mediratta",
    author_email="tanya@example.com",
    description="A Python package for TOPSIS decision making",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_tanya_102303077.topsis:run"
        ]
    },
    python_requires=">=3.6",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
