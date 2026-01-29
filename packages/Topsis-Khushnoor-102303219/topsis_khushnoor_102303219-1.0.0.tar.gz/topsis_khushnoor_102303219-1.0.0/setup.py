from setuptools import setup, find_packages

setup(
    name="Topsis-Khushnoor-102303219",
    version="1.0.0",
    author="Khushnoor Kaur",
    description="A Python package for TOPSIS MCDM problems",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=['pandas', 'numpy'],
    entry_points={
        'console_scripts': [
            'topsis = topsis_bin.topsis:main',
        ],
    },
)