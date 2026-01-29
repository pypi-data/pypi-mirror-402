from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bongram",
    version="0.1.1",
    author="Triazov Kirill",
    author_email="contact@triazov.ru",
    description="Фреймворк для мгновенного создания Telegram-ботов на готовых шаблонах",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/THWEDOKA/bongram",
    project_urls={
        "Homepage": "https://triazov.ru",
        "Bug Reports": "https://github.com/THWEDOKA/bongram/issues",
        "Source": "https://github.com/THWEDOKA/bongram",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.8",
    install_requires=[
        "aiogram>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "bongram=bongram.cli:main",
        ],
    },
    include_package_data=True,
)
