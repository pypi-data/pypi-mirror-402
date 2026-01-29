# setup.py
from setuptools import setup, find_packages

setup(
    name="trading-calendar-szse",
    version="1.0.0",
    author="忍冬",
    description="深交所交易日历Python接口",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/trading-calendar-szse",  # 替换为你的GitHub地址
    packages=find_packages(),
    install_requires=[
        "requests>=2.0.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)