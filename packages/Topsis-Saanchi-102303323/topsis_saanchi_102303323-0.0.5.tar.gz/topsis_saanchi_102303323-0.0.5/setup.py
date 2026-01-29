from setuptools import setup, find_packages

setup(
    name="Topsis_Saanchi_102303323",
    version="0.0.5",
    author="Saanchi",
    author_email="saanchigupta230@gmail.com",
    description="A Python package for TOPSIS method",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["numpy", "pandas"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_saanchi_102303323.topsis:main"
        ]
    },
    python_requires=">=3.7",
)



