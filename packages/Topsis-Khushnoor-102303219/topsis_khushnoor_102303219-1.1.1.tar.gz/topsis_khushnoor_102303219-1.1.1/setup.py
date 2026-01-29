from setuptools import setup, find_packages

setup(
    name="Topsis-Khushnoor-102303219",
    version="1.1.1",
    author="Khushnoor Kaur",
    author_email="kkaur1_be23@thapar.edu",
    description="A Python package for TOPSIS MCDM problems",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/KKaur170/Topsis-Khushnoor-102303219",
    packages=find_packages(),
    install_requires=['pandas', 'numpy'],
    entry_points={
        'console_scripts': [
            'topsis = topsis_bin.topsis:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)