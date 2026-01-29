from setuptools import setup, find_packages
import os

# Read README for long description
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
long_description = ""
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()

# Read requirements
requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
requirements = []
if os.path.exists(requirements_path):
    with open(requirements_path, "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="networkdoctor",
    version="2.1.3",
    author="frankvena25",
    author_email="frankvenas25@gmail.com",
    maintainer="frankvena25",
    maintainer_email="frankvenas25@gmail.com",
    description="Ultimate AI-Powered Network Diagnostic Tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/frankvena25/NetworkDoctor",
    project_urls={
        "Homepage": "https://github.com/frankvena25/NetworkDoctor",
        "Documentation": "https://github.com/frankvena25/NetworkDoctor/blob/main/README.md",
        "Repository": "https://github.com/frankvena25/NetworkDoctor",
        "Issues": "https://github.com/frankvena25/NetworkDoctor/issues",
        "Bug Tracker": "https://github.com/frankvena25/NetworkDoctor/issues",
    },
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "networkdoctor=networkdoctor.main:main",
            "ndoc=networkdoctor.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "Topic :: System :: Networking",
        "Topic :: System :: Networking :: Monitoring",
        "Topic :: Internet",
        "Topic :: Security",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords=[
        "network",
        "diagnostic",
        "troubleshooting",
        "ai",
        "network-analysis",
        "network-monitoring",
        "dns",
        "ssl",
        "security",
        "performance",
        "network-health",
    ],
    # Include data files
    include_package_data=True,
    package_data={
        "networkdoctor": [
            "data/*.json",
        ],
    },
    license="MIT",
)
