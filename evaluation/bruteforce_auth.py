import time
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()

def main():
    target_hash = input("Paste Argon2 hash from DB: ").strip()

    # possible simple passwords
    candidates = [
        "password", "123456", "123456789", "12345678", "password", "qwerty123", "qwerty1",
        "111111", "12345", "secret", "123123", "1234567890", "1234567", "000000", "qwerty",
        "abc123", "password1", "iloveyou", "11111111", "dragon","monkey"
    ]

    t0 = time.perf_counter()
    tried = 0
    found = None

    for pw in candidates:
        tried += 1
        try:
            if ph.verify(target_hash, pw):
                found = pw
                break
        except VerifyMismatchError:
            pass
        except Exception:
            pass

    t1 = time.perf_counter()
    elapsed = t1 - t0
    rate = tried / elapsed if elapsed > 0 else 0

    print(f"Tried {tried} passwords in {elapsed:.3f}s => {rate:.1f} attempts/sec")
    print("Found:", found)

if __name__ == "__main__":
    main()
