from setuptools import setup, find_packages

setup(
    name="Topsis-Yashika-102303439",
    version="1.0.0",
    author="Yashika",
    author_email="yashikagarg1508@gmail.com",
    description="A Python package for TOPSIS method",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    python_requires=">=3.7",
)
