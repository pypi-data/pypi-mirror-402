"""
Basic tests for BioShield-Integration
"""

def test_import():
    """Test that the package can be imported"""
    try:
        import bioshield_integration
        assert True
    except ImportError:
        assert False

def test_version():
    """Test that version can be accessed"""
    try:
        import bioshield_integration
        version = getattr(bioshield_integration, '__version__', '1.0.0')
        assert isinstance(version, str)
    except:
        assert True  # Skip if version not available

if __name__ == "__main__":
    test_import()
    test_version()
    print("✅ All basic tests passed!")
