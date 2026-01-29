from setuptools import setup, find_packages
import os

# Read long description from README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

requirements = [
    "web3==7.14.0",
    'python-dotenv==1.0.0',
    'pymongo==4.13.2',
    'cryptography==41.0.7',
    'apscheduler'   
]

# Read requirements
try:
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
except FileNotFoundError:
    pass 

setup(
    name="cryp-payment",
    version="0.1.1",
    author="wolfs code",
    author_email="wolfs.code.work@gmail.com",
    description="A cryptocurrency payment processing system for BSC",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wolfgang-99/cryp-payment",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=22.0",
            "flake8>=5.0",
            "mypy>=0.990",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)