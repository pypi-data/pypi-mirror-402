"""Minimal test code for tfm"""

from skilleter_tfm.rfm import tfm

def test_tfm():
    """Very basic test"""

    sys.argv = [sys.argv[0], '--help']
    tfm()
