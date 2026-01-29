from setuptools import setup, find_packages

setup(
    name="NR7",
    version="1.0.0",
    author="NexLangPy",
    author_email="nasrpy99@gmail.com",
    description="NR7 package with native Devil core",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://t.me/NexLangPy",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "nr7": ["Devil.so"],
    },
    python_requires=">=3.7",
)