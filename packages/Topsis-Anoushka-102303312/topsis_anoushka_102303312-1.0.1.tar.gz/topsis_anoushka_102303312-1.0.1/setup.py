from setuptools import setup, find_packages
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()
setup(
    name="Topsis-Anoushka-102303312",
    version="1.0.1",
    description="TOPSIS Implementation in Python",
    author="Anoushka Singh",
    author_email="anoushka@example.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis.topsis:run"
        ]
    }
)
