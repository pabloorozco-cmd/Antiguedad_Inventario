from src.auth import hash_pin, verify_pin


def test_pin_hash_roundtrip():
    hashed = hash_pin("83917428", iterations=100_000, salt_hex="01" * 16)
    assert hashed.startswith("pbkdf2_sha256$100000$")
    assert "83917428" not in hashed
    assert verify_pin("83917428", hashed)
    assert not verify_pin("83917429", hashed)


def test_pin_rejects_malformed_hash_and_short_values():
    assert not verify_pin("123456", "text")
    assert not verify_pin("123456", "pbkdf2_sha256$999$01$01")
    try:
        hash_pin("123")
    except ValueError:
        pass
    else:
        raise AssertionError("PIN corto aceptado")
