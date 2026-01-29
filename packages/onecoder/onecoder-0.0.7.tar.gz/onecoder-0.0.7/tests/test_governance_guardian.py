
import pytest
import sys
import os
import types
from unittest.mock import MagicMock, patch

# --- Mocking onecore before import ---
# This is necessary because the rust extension `onecore` might not be built in the test env
sys.modules["onecore"] = MagicMock()

# Import the class under test
from onecoder.governance.guardian import GovernanceGuardian

@pytest.fixture
def guardian():
    # Patch __init__ to bypass Rust backend initialization for pure logic testing
    with patch.object(GovernanceGuardian, '__init__', return_value=None):
        g = GovernanceGuardian()
        # Manually set logger as it would be in __init__
        g.logger = MagicMock()
        return g

def test_validate_staged_files_impl_only(guardian):
    """
    Test that implementation files without tests are rejected.
    """
    files = ['src/feature.ts', 'docs/readme.md']
    is_safe, msg, _ = guardian.validate_staged_files(files)
    
    assert is_safe is False
    assert "SPEC-GOV-013" in msg

def test_validate_staged_files_impl_and_tests(guardian):
    """
    Test that implementation files WITH tests are accepted.
    """
    files = ['src/feature.ts', 'src/feature.test.ts']
    is_safe, msg, _ = guardian.validate_staged_files(files)
    
    assert is_safe is True

def test_validate_staged_files_docs_only(guardian):
    """
    Test that docs-only changes are accepted without tests.
    """
    files = ['docs/readme.md', 'ops/config.yaml']
    is_safe, msg, _ = guardian.validate_staged_files(files)
    
    assert is_safe is True

def test_validate_staged_files_override(guardian):
    """
    Test that providing a valid reason overrides the check.
    """
    files = ['src/feature.ts']
    reason = "Critical hotfix logic verification"
    is_safe, msg, meta = guardian.validate_staged_files(files, reason=reason)
    
    assert is_safe is True
    assert meta.get("override") is True
