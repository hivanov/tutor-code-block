"""
Setup script for tutor-code-block (Tutor plugin & Open edX XBlock).
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
