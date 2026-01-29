from setuptools import setup, find_packages

setup(
    name="Topsis-ArunMahajan-102303346",
    version="1.0.0",
    author="Arun Mahajan",
    author_email="your_real_email@gmail.com",
    description="TOPSIS implementation using Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["numpy", "pandas"],
    entry_points={
        "console_scripts": [
            "topsis=topsis.topsis:main"
        ]
    },
)
