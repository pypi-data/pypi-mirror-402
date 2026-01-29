
from setuptools import setup, find_packages

setup(
    name="Topsis-Harsaihj-123456",
    version="1.0.0",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_harsaihj_123456.topsis:main"
        ]
    },
)
