from setuptools import setup, find_packages

setup(
    name="Topsis-Anoushka-102303312",
    version="1.0.0",
    description="TOPSIS Implementation in Python",
    author="Anoushka Singh",
    author_email="anoushka@example.com",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis.topsis:run"
        ]
    }
)
