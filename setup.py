"""
# Copyright (C) 2024-present Open edX Community
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from pathlib import Path

from setuptools import find_packages, setup

readme_path = Path("README.md")
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="tutor-code-block",
    version="0.1.0",
    description="Tutor plugin and Open edX XBlock for interactive code blocks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="GPL-3.0-or-later",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Django",
        "Intended Audience :: Education",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "tutor>=15.0.0",
        "xblock>=1.6.0",
        "pydantic>=2.0.0",
        "pygments>=2.15.0",
    ],
    entry_points={
        "tutor.plugin.v1": [
            "code_block = tutor_code_block.plugin",
        ],
        "xblock.v1": [
            "code_block = code_block_xblock.xblock:CodeBlockXBlock",
        ],
    },
    package_data={
        "code_block_xblock": [
            "data/*.json",
            "static/css/*.css",
            "static/js/*.js",
        ],
    },
    zip_safe=False,
)
