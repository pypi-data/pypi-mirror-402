from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="toxicdev", 
    version="0.0.1",
    author="Dev",
    author_email="TeamToxiclabs@gmail.com",
    description="High-speed uploading & downloading toolkit for Telegram using Telethon",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BtwSiya/toxicdev",
    packages=find_packages(),
    install_requires=[
        "telethon",
        "telethon-tgcrypto",
        "aiofiles"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
