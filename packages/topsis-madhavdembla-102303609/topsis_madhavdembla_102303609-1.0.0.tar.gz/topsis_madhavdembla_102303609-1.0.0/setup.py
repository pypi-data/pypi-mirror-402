from setuptools import setup, find_packages

setup(
    name="topsis-madhavdembla-102303609",
    version="1.0.0",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        'console_scripts': [
            'topsis=topsis.topsis:main'
        ]
    },
    author="Madhav Dembla",
    description="TOPSIS implementation using Python",
    long_description="This package implements TOPSIS for multi-criteria decision making.",
    long_description_content_type="text/plain",
)
