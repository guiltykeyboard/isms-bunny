from app import auth_utils


def test_password_hash_and_verify():
    pw = "S3cretPass!"
    h = auth_utils.hash_password(pw)
    assert auth_utils.verify_password(pw, h)


def test_totp_roundtrip():
    secret = auth_utils.generate_totp_secret()
    code = auth_utils.get_totp_now(secret)
    assert auth_utils.verify_totp(secret, code)
