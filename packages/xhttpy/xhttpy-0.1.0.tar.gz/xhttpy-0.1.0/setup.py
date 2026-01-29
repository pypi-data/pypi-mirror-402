from setuptools import setup, find_packages

setup(
    name="xhttpy",
    version="0.1.0",
    author="Yam",
    author_email="haoshaochun@gmail.com",
    description="Unified sync/async HTTP client supporting httpx and aiohttp backends.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/hscspring/xhttpy.git",
    packages=find_packages(),
    install_requires=[
        "httpx",
        "aiohttp",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)