from setuptools import setup, find_packages

setup(
    name="Topsis-Vandana-102303443",
    version="1.0.0",
    author="Vandana",
    author_email="vandanaverma2506@gmail.com",
    description="Python package for TOPSIS method",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_vandana_102303443.topsis:__main__"
        ]
    },
    python_requires=">=3.7",
)
