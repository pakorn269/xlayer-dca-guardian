import sys
from unittest.mock import MagicMock
import pytest

sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.pyplot'] = MagicMock()
sys.exit(pytest.main(['tests/']))
