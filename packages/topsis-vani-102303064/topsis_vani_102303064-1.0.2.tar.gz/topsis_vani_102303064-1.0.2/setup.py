from setuptools import setup, find_packages

setup(
    name="topsis-vani-102303064",
    version="1.0.2",
    author="Vani",
    author_email="vanimohindru7@gmail.com",
    description="TOPSIS implementation as a Python package",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_vani_102303064.pred_as1:main"
        ]
    },
    license="MIT",
    python_requires=">=3.8",
)
