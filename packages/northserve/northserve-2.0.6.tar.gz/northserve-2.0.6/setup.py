#!/usr/bin/env python3
"""Setup script for NorthServing."""

from setuptools import setup, find_packages
from pathlib import Path
import os
import re

# Read version from pyproject.toml
def get_version():
    """Read version from pyproject.toml."""
    pyproject_path = Path(__file__).parent / "pyproject.toml"
    if pyproject_path.exists():
        content = pyproject_path.read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
        if match:
            return match.group(1)
    raise ValueError("Version not found in pyproject.toml")

VERSION = get_version()

# Read the README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

# 获取所有数据文件
def get_data_files(directory):
    """获取目录下的所有文件（相对路径）"""
    data_files = []
    base_path = Path(__file__).parent
    data_dir = base_path / directory

    if not data_dir.exists():
        return []

    for root, dirs, files in os.walk(data_dir):
        for file in files:
            file_path = Path(root) / file
            # 获取相对于项目根目录的路径
            rel_path = file_path.relative_to(base_path)
            data_files.append(str(rel_path))

    return data_files

# 收集所有数据文件
all_data_files = []
all_data_files.extend(get_data_files('configs'))
all_data_files.extend(get_data_files('yaml_templates'))
all_data_files.extend(get_data_files('benchmark'))

setup(
    name="northserve",
    version=VERSION,
    author="NorthServing Team",
    description="A one-click LLM serving deployment tool for Kubernetes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/china-qijizhifeng/NorthServing",
    packages=find_packages(exclude=["tests", "tests.*", "tools"]),
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "northserve=northserve.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    include_package_data=True,
    # 将数据文件作为包数据包含
    package_data={
        '': all_data_files,
    },
)
