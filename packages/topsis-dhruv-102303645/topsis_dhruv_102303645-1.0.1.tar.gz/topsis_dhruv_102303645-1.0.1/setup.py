from setuptools import setup, find_packages

setup(
    name="topsis-dhruv-102303645",
    version="1.0.1",
    author="Dhruv",
    author_email="dkamboj_be23@thapar.edu",
    description="TOPSIS command line tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["numpy", "pandas"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_dhruv_102303645.topsis_code:main"
        ]
    },
    python_requires=">=3.7",
)
