import base64, time, os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def derive(password: str, salt: bytes, iters=200_000) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iters,
        backend=default_backend(),
    )
    return kdf.derive(password.encode("utf-8"))

def main():
    # Paste from DB (base64-encode them for easy copy)
    salt_b64 = input("kdf_salt (base64): ").strip()
    nonce_b64 = input("nonce (base64): ").strip()
    ct_b64 = input("ciphertext (base64): ").strip()

    salt = base64.b64decode(salt_b64)
    nonce = base64.b64decode(nonce_b64)
    ct = base64.b64decode(ct_b64)

    candidates = ["password", "Password1", "Password123", "letmein", "admin"]

    t0 = time.perf_counter()
    tried = 0
    found = None

    for pw in candidates:
        tried += 1
        try:
            key = derive(pw, salt)
            pt = AESGCM(key).decrypt(nonce, ct, None)
            # If decrypt succeeds, password guess is correct
            found = pw
            print("Decrypted preview:", pt[:80])
            break
        except Exception:
            pass

    t1 = time.perf_counter()
    elapsed = t1 - t0
    print(f"Tried {tried} in {elapsed:.3f}s => {tried/elapsed:.1f} attempts/sec")
    print("Found:", found)

if __name__ == "__main__":
    main()
