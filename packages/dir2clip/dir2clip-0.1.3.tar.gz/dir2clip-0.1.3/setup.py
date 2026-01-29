from setuptools import setup, find_packages

setup(
    name="dir2clip",
    version="0.1.3",
    description="A CLI tool to flatten directory contents to clipboard for LLM context.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="alextereshyt",
    author_email="alextereshyt@gmail.com",
    url="https://github.com/alextereshyt/Dir2Clip",
    packages=find_packages(),
    install_requires=[
        "pyperclip",
    ],
    entry_points={
        "console_scripts": [
            "dir2clip=dir2clip.core:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
