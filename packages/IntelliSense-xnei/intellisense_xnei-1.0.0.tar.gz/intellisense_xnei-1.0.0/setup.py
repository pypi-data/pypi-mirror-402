# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name="IntelliSense-xnei",
    version="1.0.0",
    packages=find_packages(),
    install_requires=["tkinter","customtkinter"],
    python_requires=">=3.10",
    description="""IntelliSense-xnei is a Python package that provides a large code input window
for Tkinter and CustomTkinter with built-in automatic code completion. It supports multiple
languages including Python, TypeScript, C, C++, C#, HTML, CSS, JS, Go, Rust, Markdown, and JSON.
With this package, users can:
- Open a large input window for code writing.
- See code suggestions in the bottom-right corner as they type.
- Easily integrate automatic code completion into Tkinter or CustomTkinter GUIs.
- Quickly test and run code snippets interactively.
""",
    author="Hamza Al",
    url="https://github.com/yourusername/IntelliSense-xnei",
)
