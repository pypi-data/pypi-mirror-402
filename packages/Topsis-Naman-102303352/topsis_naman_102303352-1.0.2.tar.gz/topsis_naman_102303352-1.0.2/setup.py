from setuptools import setup, find_packages

# This reads the content of your README.md file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='Topsis-Naman-102303352',
    version='1.0.2',
    author='Naman',
    description='A Python package for TOPSIS multi-criteria decision making.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=['pandas', 'numpy'],
    entry_points={
        'console_scripts': [
            'topsis=topsis_Naman_102303352.topsis:topsis',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)