from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="pykapfinance",
    version="0.1.1",
    author="Çağrı Güngör",
    author_email="iletisim@cagrigor.com",
    description="Python client library for KAP (Kamuyu Aydınlatma Platformu) API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cagrigungor/pykap",
    license="MIT",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    keywords="kap, turkey, stock market, disclosure, finance, api, borsa istanbul, mkk",
    project_urls={
        "Bug Reports": "https://github.com/cagrigungor/pykap/issues",
        "Source": "https://github.com/cagrigungor/pykap",
        "Documentation": "https://github.com/cagrigungor/pykap/blob/main/README.md",
    },
)
