from setuptools import setup, find_packages

setup(
    name="Topsis-AryanSaini-102303666",
    version="1.0.0",
    author="Aryan",
    author_email="asaini2_be23@thapar.edu",
    description="A Python package for TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution)",
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "pandas",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'topsis=topsis_aryan.run_topsis:main',
        ],
    },
)
