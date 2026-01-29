from setuptools import setup, find_packages

setup(
    name="Topsis-Rishika-102313050",
    version="1.0.0",
    author="Rishika",
    author_email="your_email@example.com",
    description="A Python package implementing the TOPSIS method.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
    ],
    entry_points={
        'console_scripts': [
            'topsis=topsis_rishika.main:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)