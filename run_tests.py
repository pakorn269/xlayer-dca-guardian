import sys
from unittest.mock import MagicMock
sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.pyplot'] = MagicMock()

import pytest
sys.exit(pytest.main(['tests/']))
