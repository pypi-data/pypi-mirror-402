"""Test configuration."""

import sys
from pathlib import Path

# Add the package to the path
package_dir = Path(__file__).parent.parent
sys.path.insert(0, str(package_dir))
