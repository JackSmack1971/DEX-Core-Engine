import pytest

from security.secure_memory import locked_memory, secure_zero_memory


def test_secure_zero_memory():
    buf = bytearray(b"secret")
    secure_zero_memory(buf)
    assert all(b == 0 for b in buf)


def test_locked_memory_zeroes_on_exit():
    try:
        with locked_memory(b"secret") as mem:
            assert bytes(mem) == b"secret"
        assert bytes(mem) == b"\x00" * 6
    except OSError:
        pytest.skip("mlock not supported")
