from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="git-commit-summary",
    version="1.0.0",
    author="Sai Annam",
    author_email="contact@mraskchay.com",  # Placeholder or generic if not known
    description="A powerful CLI tool to summarize git commits with rich visual feedback.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/otaku0304/git-commit-summary",
    py_modules=["summary"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: Software Development :: Version Control :: Git",
    ],
    install_requires=[
        "colorama>=0.4.6",
    ],
    entry_points={
        "console_scripts": [
            "git-commit-summary=summary:main",
        ],
    },
    python_requires=">=3.6",
)
