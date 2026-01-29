from setuptools import setup, find_packages

setup(
    name="Topsis-Bhavuk-102303140",
    version="0.0.4",
    author="Bhavuk Mahajan",
    author_email="bhavukmahajan007@gmail.com",
    description="TOPSIS package for MCDM problems",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["numpy", "pandas"],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "topsis=topsis_bhavuk_102303140.topsis:main"
        ]
    },
    license="MIT"
)