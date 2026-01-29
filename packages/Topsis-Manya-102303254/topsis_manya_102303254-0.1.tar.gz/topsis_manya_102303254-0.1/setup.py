
from setuptools import setup, find_packages

setup(
    name="Topsis-Manya-102303254",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy",
        "openpyxl"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_manya_102303254.topsis:main"
        ]
    },
    author="Manya Garg",
    author_email="manyagarg453@gmail.com",
    description="TOPSIS Multi-Criteria Decision Making Tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/Topsis-Manya-102303254",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
