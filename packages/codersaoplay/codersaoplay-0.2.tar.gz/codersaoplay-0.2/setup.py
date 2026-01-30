from setuptools import setup, find_packages

setup(
    name="codersaoplay",
    version="0.2",
    packages=find_packages(),
    install_requires=[
        "pygame>=2.6.1"  # Use a prebuilt wheel
    ],
    python_requires=">=3.10",  # adjust based on your version
    description="A callable Python module to play MP3 files in one line",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Jatin Ghoyal",
    author_email="codersao@gmail.com",
    license="MIT",
    url="https://github.com/codersao/codersaoplay",  # optional GitHub URL
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Microsoft :: Windows",
        "License :: OSI Approved :: MIT License",
    ],
)
