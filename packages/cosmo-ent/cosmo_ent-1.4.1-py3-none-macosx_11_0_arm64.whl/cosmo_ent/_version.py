"""Version information for cosmo-ent package.

This module defines the version of the Python package and the upstream ent version
being packaged.

Versioning scheme: {ENT_MAJOR}.{ENT_MINOR}.{PACKAGE_PATCH}
  - ENT_MAJOR.ENT_MINOR: Version of upstream ent being packaged
  - PACKAGE_PATCH: Python package-specific updates (starts at 0 for each new ent version)

Examples:
  - 1.4.0: First release packaging ent 1.4
  - 1.4.1: Bugfix/improvement to Python packaging for ent 1.4
  - 1.5.0: First release packaging ent 1.5
"""

# Python package version
__version__ = "1.4.1"

# Commit hash from https://github.com/Fourmilab/ent_random_sequence_tester to build
ENT_COMMIT_HASH = "388d2cc499813e6865e833a66b612172a1674efc"
