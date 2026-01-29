"""
agent-android - Android ADB automation CLI tool

Setup configuration for PyPI distribution
"""

from setuptools import setup, find_packages
import os

# 读取 README 文件
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()

setup(
    name="agent-android",
    version="1.1.2",
    author="Fast2x",
    author_email="contact@fast2x.com",
    description="Android ADB automation CLI tool - Designed for AI Agents",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/Fast2x/agent-android",
    project_urls={
        "Bug Reports": "https://github.com/Fast2x/agent-android/issues",
        "Source": "https://github.com/Fast2x/agent-android",
        "Documentation": "https://github.com/Fast2x/agent-android/blob/main/README.md",
    },
    packages=find_packages(exclude=["tests", "tests.*", "docs", "examples", "*.tmp", "*.bak"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "python-dotenv>=0.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "pylint>=2.12.0",
            "mypy>=0.950",
        ],
    },
    entry_points={
        "console_scripts": [
            "agent-android=core.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="android automation adb testing rpa ai agent cli mobile screenshot uiautomator",
    package_data={
        "": ["*.md", "*.txt", "*.bat"],
    },
)
