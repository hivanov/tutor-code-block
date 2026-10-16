"""
Tutor plugin for Code Block XBlock with syntax highlighting, line numbers, and copy button.
"""

from tutor import hooks

# Configuration defaults
hooks.Filters.CONFIG_DEFAULTS.add_items(
    [
        ("CODE_BLOCK_ENABLE", True),
        ("CODE_BLOCK_PIP_REQUIREMENT", "tutor-code-block"),
    ]
)

# Injects the XBlock pip dependency and settings into Open edX LMS & CMS Docker image builds
hooks.Filters.ENV_PATCHES.add_items(
    [
        (
            "openedx-dockerfile-post-python-requirements",
            """
# Install Code Block XBlock
RUN pip install {{ CODE_BLOCK_PIP_REQUIREMENT }}
""",
        ),
        (
            "openedx-lms-common-settings",
            """
# Code Block XBlock Feature Flags
FEATURES["ENABLE_CODE_BLOCK_XBLOCK"] = True
""",
        ),
        (
            "openedx-cms-common-settings",
            """
# Code Block XBlock Feature Flags
FEATURES["ENABLE_CODE_BLOCK_XBLOCK"] = True
""",
        ),
    ]
)
