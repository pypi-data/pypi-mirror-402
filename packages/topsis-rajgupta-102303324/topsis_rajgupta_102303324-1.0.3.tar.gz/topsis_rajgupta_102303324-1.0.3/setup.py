from setuptools import setup, find_packages

setup(
    name="topsis-rajgupta-102303324",
    version="1.0.3",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        'console_scripts': [
            'topsis=topsis.topsis:main'
        ]
    },
    python_requires=">=3.7",
    author="Raj Gupta",
    description="TOPSIS implementation using Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)