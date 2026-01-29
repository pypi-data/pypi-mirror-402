from setuptools import setup, find_packages

setup(
    name="topsis-shivank-102303655",
    version="0.2.1",
    author="Shivank Bhatia",
    author_email="bhatiashivankwork@gmail.com",
    description="Command line implementation of TOPSIS for MCDM problems",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(),
    install_requires=["pandas"],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "topsis=topsis_shivank.run_topsis:main"
        ]
    },
)
