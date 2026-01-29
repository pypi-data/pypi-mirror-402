import slidex


def test_module_imports():
    assert slidex.Presentation is not None
    assert slidex.SlidexError is not None
