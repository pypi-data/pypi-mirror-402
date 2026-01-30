"""skilleter_tfm package."""

# Prefer a sibling checkout of skilleter-modules (for popup, etc.) over any
# installed version when developing locally.
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_LOCAL_MODULES = _REPO_ROOT.parent / 'skilleter-modules'

if _LOCAL_MODULES.is_dir():
	local_path = str(_LOCAL_MODULES)
	if local_path not in sys.path:
		sys.path.insert(0, local_path)
