"""
Agentify SDK - Agent Standard v1 Implementation
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="agentify-sdk",
    version="1.0.0",
    author="Jonas Mößler",
    author_email="jonas@agentify.ai",
    description="Agent Standard v1 - Universal agent wrapper with ethics, oversight, and health monitoring",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JonasDEMA/agentify_os",
    project_urls={
        "Bug Tracker": "https://github.com/JonasDEMA/agentify_os/issues",
        "Documentation": "https://github.com/JonasDEMA/agentify_os/tree/main/core/agent_standard",
        "Source Code": "https://github.com/JonasDEMA/agentify_os",
    },
    packages=find_packages(where=".", include=["core", "core.*", "platform", "platform.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "typing-extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
        ],
        "langchain": [
            "langchain>=0.1.0",
            "langchain-core>=0.1.0",
        ],
        "openai": [
            "openai>=1.0.0",
        ],
        "anthropic": [
            "anthropic>=0.18.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "agentify=core.agent_standard.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "core.agent_standard": [
            "templates/*.json",
            "examples/*.json",
            "schemas/*.json",
        ],
    },
    keywords=[
        "agent",
        "ai",
        "ethics",
        "oversight",
        "health-monitoring",
        "agent-standard",
        "agentify",
        "agentic-economy",
        "multi-agent",
        "langchain",
    ],
    zip_safe=False,
)

