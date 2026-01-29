from setuptools import setup

setup(
    name="Topsis-Pragati-102303310", # REPLACE WITH YOUR NAME-ROLLNUMBER 
    version="1.0.0",
    author="Pragati Arora",
    description="A Python package for TOPSIS decision making",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages=['topsis'],
    install_requires=['pandas', 'numpy'], # These are the tools your code needs
    entry_points={
        'console_scripts': [
            'topsis=topsis.topsis:main', # This lets users type 'topsis' in terminal
        ],
    },
)