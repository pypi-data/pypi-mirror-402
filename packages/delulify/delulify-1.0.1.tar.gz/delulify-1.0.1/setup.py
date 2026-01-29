from setuptools import setup, find_packages

setup(
    name="delulify",
    version="1.0.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "delulify=delulify.__main__:main",  # Creates the `delulify` CLI command
        ],
    },
    description="A Python CLI wrapper with emotionally supportive or roasting error messages for crashed scripts.",
    author="Vaishnavi Jadhav",
    author_email="sonapjadhav05@gmail.com",  # Replace with your email
    url="https://github.com/VaishJadhavVJ/delulify.git", 
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    long_description="""
    Delulify is a Python CLI tool that wraps around your Python scripts. When your script crashes, 
    Delulify intercepts the traceback and provides you with emotionally supportive—or brutally 
    roast-worthy—error messages instead. Choose your vibe!
    """,
    long_description_content_type="text/markdown",
)