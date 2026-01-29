from setuptools import setup, find_packages

setup(
    name="Topsis-manleen-102303599",
    version="1.0.0",
    description="Implementation of TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)",
    author="Manleen Kaur",
    author_email="kaurmanleen05@gmail.com",  # use your real email
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_engine.cli:main"
        ]
    },
    python_requires=">=3.8",
)
