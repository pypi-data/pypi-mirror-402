from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="depalert",
    version="0.0.1",
    author="CyberGabi Team",
    author_email="security@chainthreatwall.com",
    description="Security placeholder for DepAlert tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CyberGabiSoft/depalert",
    project_urls={
        "Bug Tracker": "https://github.com/CyberGabiSoft/depalert/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 1 - Planning",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.6",
)
