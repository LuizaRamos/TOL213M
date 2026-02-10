import os, time, statistics
from argon2 import PasswordHasher
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ph = PasswordHasher()  # Argon2id defaults

def derive_master_key(password: str, salt: bytes, iters: int = 200_000) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iters,
        backend=default_backend()
    )
    return kdf.derive(password.encode("utf-8"))

def bench(fn, reps=20):
    times = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)  # ms
    return {
        "mean_ms": statistics.mean(times),
        "p95_ms": statistics.quantiles(times, n=20)[18],  # approx p95
        "min_ms": min(times),
        "max_ms": max(times),
    }

def main():
    password = "Password123"
    wrong = "Password124"
    salt = os.urandom(16)

    # 1) Argon2 hash + verify
    pw_hash = ph.hash(password)

    auth_ok = bench(lambda: ph.verify(pw_hash, password), reps=30)
    auth_bad = bench(lambda: (ph.verify(pw_hash, wrong) if False else ph.verify(pw_hash, wrong)), reps=30)

    # 2) PBKDF2 derive
    kdf_stats = bench(lambda: derive_master_key(password, salt), reps=30)

    # 3) AES-GCM encrypt/decrypt across sizes
    key = derive_master_key(password, salt)
    aesgcm = AESGCM(key)

    sizes = [1_024, 10_240, 102_400, 1_048_576, 5_242_880]  # 1KB,10KB,100KB,1MB,5MB
    results = []

    for n in sizes:
        data = os.urandom(n)
        nonce = os.urandom(12)

        enc_stats = bench(lambda: aesgcm.encrypt(nonce, data, None), reps=15)

        ct = aesgcm.encrypt(nonce, data, None)
        dec_stats = bench(lambda: aesgcm.decrypt(nonce, ct, None), reps=15)

        results.append((n, enc_stats, dec_stats))

    print("\n=== Authentication ===")
    print("Argon2 verify (correct):", auth_ok)
    print("Argon2 verify (wrong):  ", auth_bad)
    print("PBKDF2 derive:", kdf_stats)

    print("\n=== AES-GCM ===")
    for n, enc, dec in results:
        print(f"{n} bytes | enc mean {enc['mean_ms']:.2f}ms (p95 {enc['p95_ms']:.2f}) | "
              f"dec mean {dec['mean_ms']:.2f}ms (p95 {dec['p95_ms']:.2f})")

if __name__ == "__main__":
    main()
