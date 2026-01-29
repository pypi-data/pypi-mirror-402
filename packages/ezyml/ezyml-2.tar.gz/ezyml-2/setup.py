from setuptools import setup, find_packages

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ezyml",
    version="2",
    author="Raktim Kalita",
    author_email="raktimkalita.ai@gmail.com",
    description="A lightweight tool to train, evaluate, and export ML models in one line.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Rktim/ezyml",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires='>=3.7',
    install_requires=[
        'scikit-learn',
        'pandas',
        'numpy',
        'xgboost',
    ],
    entry_points={
        'console_scripts': [
            'ezyml=ezyml.cli:main',
        ],
    },
)


