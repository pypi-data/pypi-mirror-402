from setuptools import setup, find_packages

setup(
    name="Topsis-Swikriti-102303440",
    version="0.0.1",
    author="Swikriti",
    author_email="srathore_be23@thapar.edu",
    description="A Python package for TOPSIS method",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        'console_scripts': [
            'topsis=topsis.topsis:main'
        ]
    }
)
