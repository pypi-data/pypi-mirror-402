from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="topsis-saumyakumari-102303161",
    version="1.0.2",
    author="Saumya Kumari",
    description="Python package for TOPSIS method",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.6",
    entry_points={
        'console_scripts': [
            'topsis=Topsis_SaumyaKumari_102303161.topsis:main',
        ],
    },
)
