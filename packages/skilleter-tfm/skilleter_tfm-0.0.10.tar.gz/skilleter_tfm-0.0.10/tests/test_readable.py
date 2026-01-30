"""Minimal test code for tfm"""

def test_tfm_importable():
    """Ensure the main entry point is available without running curses."""

    from skilleter_tfm import tfm as tfm_mod

    assert callable(tfm_mod.tfm)
