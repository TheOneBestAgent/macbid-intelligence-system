"""Setup script for API Endpoint Discovery Scraper."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="api-endpoint-scraper",
    version="0.1.0",
    author="API Scraper Team",
    author_email="team@example.com",
    description="A comprehensive tool for discovering API endpoints from web applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/api-endpoint-scraper",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Security",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Networking :: Monitoring",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.10.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "api-scraper=cli:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["config/*.yaml"],
    },
    keywords=[
        "api", "endpoint", "discovery", "scraping", "security", "testing",
        "web", "automation", "reconnaissance", "pentesting"
    ],
    project_urls={
        "Bug Reports": "https://github.com/example/api-endpoint-scraper/issues",
        "Source": "https://github.com/example/api-endpoint-scraper",
        "Documentation": "https://github.com/example/api-endpoint-scraper/wiki",
    },
) 