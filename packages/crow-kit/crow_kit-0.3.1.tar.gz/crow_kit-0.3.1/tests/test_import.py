def test_import():
    import crow_kit
    assert hasattr(crow_kit, "__version__")
    assert crow_kit.__version__ == "0.3.0"