from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

from application.core.logger import main_logger as log

HASH_VERIFIER: PasswordHasher = PasswordHasher()


def verify_hash(hashed_token: str, plain_token: str) -> bool:
    """Универсальная функция для проверки соответствия значения его хешу (свертке)."""
    try:
        HASH_VERIFIER.verify(hashed_token, plain_token)
    except VerifyMismatchError:
        raise
    except InvalidHashError:
        log.exception('Critical Config Error: Hash in .env is malformed')
        raise
    except Exception:
        log.exception('Unexpected error during verification')
        raise
