from setuptools import setup, find_packages

setup(
    name="topsis-hardik-102303494",
    version="0.1.1",
    packages=find_packages(),
    install_requires=["numpy", "pandas"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_hardik_102303494.cli:main"
        ]
    },
    author="Hardik",
    description="TOPSIS implementation for decision making",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
)
