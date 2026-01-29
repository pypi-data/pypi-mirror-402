from setuptools import setup, find_packages

setup(
    name="topsis-riddhi-102483079",
    version="1.0.0",
    author="Riddhi",
    author_email="riddhi.jain15102004@gmail.com",
    description="Python package for TOPSIS method",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_vandana_123456.topsis:__main__"
        ]
    },
    python_requires=">=3.7",
)
