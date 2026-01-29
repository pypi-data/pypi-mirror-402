from setuptools import setup, find_packages

setup(
    name="Topsis-Shaurya-102317151",
    version="1.0.1",
    author="Shaurya Verma",
    author_email="sverma1_be23@thapar.edu",
    description="A package for Topsis",
    long_description="This is a library for performing TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution).",
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=['pandas', 'numpy'],
    entry_points={
        'console_scripts': [
            'topsis=Topsis_Shaurya_102317151.topsis:main',
        ],
    },
)