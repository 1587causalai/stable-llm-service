from setuptools import setup, find_packages
import os

# 读取README.md内容作为长描述
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md"), "r", encoding="utf-8") as f:
    long_description = f.read()

# 读取requirements.txt文件获取依赖列表
with open(os.path.join(here, "requirements.txt"), "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="stable-llm-service",
    version="0.1.0",
    author="StableLLM Team",
    author_email="example@example.com",
    description="稳定可靠的大模型调用中间层",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/stable-llm-service",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/stable-llm-service/issues",
        "Documentation": "https://github.com/yourusername/stable-llm-service",
        "Source Code": "https://github.com/yourusername/stable-llm-service",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="llm, ai, openai, anthropic, gemini, api, service, wrapper, stability",
    packages=find_packages(exclude=["tests", "examples"]),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "stable-llm-chat=stable_llm_service.cli:chat_command",
            "stable-llm-analyze=stable_llm_service.cli:analyze_command",
        ],
    },
) 