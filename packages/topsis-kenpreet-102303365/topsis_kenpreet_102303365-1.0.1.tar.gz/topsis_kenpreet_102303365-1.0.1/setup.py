from setuptools import setup, find_packages

setup(
    name="topsis-kenpreet-102303365",
    version="1.0.1",   # 👈 MUST be 1.0.1
    author="Kenpreet Singh Thukral",
    description="TOPSIS implementation using Python",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis.topsis:topsis_main"
        ]
    },
)

