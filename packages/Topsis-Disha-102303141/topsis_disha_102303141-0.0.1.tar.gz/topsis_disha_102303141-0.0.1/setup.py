from setuptools import setup, find_packages

setup(
    name="Topsis-Disha-102303141",
    version="0.0.1",
    author="Disha Malik",
    author_email="dmalik_be23@thapar.edu",
    description="TOPSIS package for MCDM problems",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["numpy", "pandas"],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "topsis=topsis_disha_102303141.topsis:main"
        ]
    },
    license="MIT"
)
