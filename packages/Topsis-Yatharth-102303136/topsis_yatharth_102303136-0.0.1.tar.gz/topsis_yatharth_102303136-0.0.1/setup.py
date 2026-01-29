from setuptools import setup, find_packages

setup(
    name="Topsis-Yatharth-102303136",
    version="0.0.1",
    author="Yatharth Sharma",
    author_email="yatharth04sharma@gmail.com",
    description="A Python package for TOPSIS multi-criteria decision making",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_yatharth_102303136.topsis:main"
        ]
    },
    python_requires=">=3.6",
)
