from setuptools import setup, find_packages

setup(
    name="telegram_async",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[
        "aiohttp",
        "rich"
    ],
)
