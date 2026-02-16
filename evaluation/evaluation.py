from __future__ import annotations

import sys
import os
import time
import csv
import random
from pathlib import Path
from typing import List, Tuple, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.app import create_app
from src.persistences.models import db
from src.persistences.models.User import User
from src.persistences.models.Text import Text
from src.services.implementations.TextServiceImplementation import TextServiceImplementation

EVAL_DB_PATH = PROJECT_ROOT / "src" / "Instance" / "eval.db"
TEXT_DIR = PROJECT_ROOT / "evaluation" / "texts"

TEXT_SIZES = [1_024, 10_240, 102_400, 1_048_576]  # 1KB, 10KB, 100KB, 1MB

PBKDF2_ITERS = 200_000
MASTER_KEY_LEN = 32

# Reproducibility for benchmarks (stable dataset generation from your text corpus)
RANDOM_SEED = 7278

AUTH_REPEATS = 20
CRYPTO_REPEATS = 10

RESULTS_DIR = PROJECT_ROOT / "evaluation"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = RESULTS_DIR / "eval_metrics.csv"

# Helpers: KDF / key derivation
def derive_master_key(password: str, salt: bytes, iterations: int = PBKDF2_ITERS) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=MASTER_KEY_LEN,
        salt=salt,
        iterations=iterations,
        backend=default_backend(),
    )
    return kdf.derive(password.encode("utf-8"))


# Helpers: text loading + exact-size plaintext construction
def load_text(text_dir: Path) -> List[bytes]:
    blobs: List[bytes] = []
    if not text_dir.exists():
        raise RuntimeError(f"Directory not found: {text_dir}")

    for p in sorted(text_dir.glob("*.txt")):
        data = p.read_bytes()
        try:
            data.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            continue
        if data.strip():
            blobs.append(data)

    if not blobs:
        raise RuntimeError(
            f"No usable UTF-8 .txt files found in {text_dir}. "
        )
    return blobs


def build_sample_bytes(target_size: int, corpus: List[bytes], rng: random.Random) -> bytes:
    out = bytearray()
    while len(out) < target_size:
        piece = rng.choice(corpus)

        # Take random slice to diversify content and avoid repeating same prefix
        if len(piece) > 4096:
            start = rng.randrange(0, len(piece) - 2048)
            end = min(len(piece), start + rng.randrange(512, 8192))
            piece = piece[start:end]

        out.extend(piece)
        out.extend(b"\n")  # separator
    return bytes(out[:target_size])


def make_text_of_exact_size(target_size: int, corpus: List[bytes], rng: random.Random) -> str:

    for _ in range(10):
        sample_bytes = build_sample_bytes(target_size, corpus, rng)
        text = sample_bytes.decode("utf-8", errors="ignore")
        b = text.encode("utf-8")
        if len(b) == target_size:
            return text
        if len(b) < target_size:
            target_size = target_size + (target_size - len(b)) + 16
            continue
        return b[:target_size].decode("utf-8", errors="ignore")

    # Fallback: accept closest
    sample_bytes = build_sample_bytes(target_size, corpus, rng)
    return sample_bytes.decode("utf-8", errors="ignore")



# Benchmark helpers
def time_call(fn, repeats: int) -> float:
    t0 = time.perf_counter()
    for _ in range(repeats):
        fn()
    t1 = time.perf_counter()
    return (t1 - t0) / repeats


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    keys = sorted(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

# Brute-force storage
def bruteforce_storage(
    user: User,
    correct_password: str,
    text_obj: Text,
    candidate_passwords: List[str],
) -> Dict[str, Any]:

    nonce = text_obj.nonce
    ciphertext = text_obj.ciphertext

    attempts = 0
    t0 = time.perf_counter()
    found_password = None

    for pw in candidate_passwords:
        attempts += 1
        try:
            key = derive_master_key(pw, user.kdf_salt)
            pt = AESGCM(key).decrypt(nonce, ciphertext, None)
            found_password = pw
            break
        except Exception:
            continue

    t1 = time.perf_counter()

    return {
        "bruteforce_attempts": attempts,
        "bruteforce_seconds": (t1 - t0),
        "bruteforce_found_password": found_password,
        "bruteforce_found_is_correct": (found_password == correct_password),
    }

def main():
    # Ensure Instance/ exists
    EVAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Delete old eval DB to keep evaluation stable and repeatable
    if EVAL_DB_PATH.exists():
        EVAL_DB_PATH.unlink()

    # Force app to use eval DB
    os.environ["DATABASE_URL"] = f"sqlite:///{EVAL_DB_PATH.resolve()}"

    # Create Flask app
    app = create_app()

    # Load plaintext (NOT encrypted) from evaluation/text/
    text = load_text(TEXT_DIR)
    rng = random.Random(RANDOM_SEED)

    # Users for evaluation (strong + weak + a few extra)
    users_spec = [
        {"username": "eval_strong", "email": "eval_strong@example.com", "password": "Str0ngPassw0rd!"},
        {"username": "eval_weak",   "email": "eval_weak@example.com",   "password": "Password123"},
        {"username": "populating0", "email": "p0@example.com",          "password": "jHydm96O"},
        {"username": "populating1", "email": "p1@example.com",          "password": "RgksoP30"},
        {"username": "populating2", "email": "p2@example.com",          "password": "!Kjfnie08"},
    ]

    metrics_rows: List[Dict[str, Any]] = []

    app = create_app()

    with app.app_context():
        db.drop_all()
        db.create_all()

        created_users: List[Tuple[User, str]] = []

        for spec in users_spec:
            u = User(username=spec["username"], email=spec["email"])

            # Measure time to hash password
            def _do_set_password():
                u.set_password(spec["password"])

            avg_set = time_call(_do_set_password, repeats=1)
            if not getattr(u, "kdf_salt", None):
                u.kdf_salt = os.urandom(16)

            db.session.add(u)
            created_users.append((u, spec["password"]))

            metrics_rows.append({
                "category": "auth",
                "operation": "set_password_hash",
                "username": spec["username"],
                "size_bytes": "",
                "avg_seconds": avg_set,
                "notes": "Argon2 password hashing during registration",
            })

        db.session.commit()

        # Benchmark check_password
        for u, pw in created_users:
            if not hasattr(u, "check_password"):
                raise RuntimeError("User model is missing check_password(). Needed for auth benchmark.")

            avg_verify = time_call(lambda: u.check_password(pw), repeats=AUTH_REPEATS)
            metrics_rows.append({
                "category": "auth",
                "operation": "check_password_verify",
                "username": u.username,
                "size_bytes": "",
                "avg_seconds": avg_verify,
                "notes": f"Argon2 verify averaged over {AUTH_REPEATS} repeats",
            })

        for u, pw in created_users:
            master_key = derive_master_key(pw, u.kdf_salt)
            service = TextServiceImplementation(master_key)

            for size in TEXT_SIZES:
                # Build plaintext from text of EXACT size (bytes)
                plaintext = make_text_of_exact_size(size, text, rng)
                size_bytes = len(plaintext.encode("utf-8"))

                # Encrypt timing
                def _do_encrypt():
                    service.encrypt_and_store(u.id, f"{u.username}_{size_bytes}B", plaintext)

                enc_avg = time_call(_do_encrypt, repeats=CRYPTO_REPEATS)

                text_obj = service.encrypt_and_store(u.id, f"{u.username}_{size_bytes}B_one", plaintext)

                # Decrypt timing
                def _do_decrypt():
                    _ = service.decrypt_for_user(text_obj)

                dec_avg = time_call(_do_decrypt, repeats=CRYPTO_REPEATS)

                # Correctness check
                decrypted = service.decrypt_for_user(text_obj)
                ok = (decrypted == plaintext)

                metrics_rows.append({
                    "category": "crypto",
                    "operation": "encrypt_store",
                    "username": u.username,
                    "size_bytes": size_bytes,
                    "avg_seconds": enc_avg,
                    "notes": f"AES-GCM encrypt+DB insert avg over {CRYPTO_REPEATS} repeats",
                })

                metrics_rows.append({
                    "category": "crypto",
                    "operation": "decrypt_read",
                    "username": u.username,
                    "size_bytes": size_bytes,
                    "avg_seconds": dec_avg,
                    "notes": f"AES-GCM decrypt+read avg over {CRYPTO_REPEATS} repeats; correct={ok}",
                })

                print(f"  - user={u.username:12s} size={size_bytes:>8}B  enc_avg={enc_avg:.6f}s  dec_avg={dec_avg:.6f}s  ok={ok}")

        # Brute-force storage (try to get weak password)
        weak_user = next(u for (u, _) in created_users if u.username == "eval_weak")
        weak_pw = next(pw for (u, pw) in created_users if u.username == "eval_weak")

        # Pick one text for weak user
        weak_text = Text.query.filter_by(user_id=weak_user.id).order_by(Text.created_at.desc()).first()
        if not weak_text:
            raise RuntimeError("No text rows found for eval_weak; expected encryption inserts to have created them.")

        candidates = [
            "123456", "password", "Password", "Password1", "Password12",
            "Password123", "password123", "qwerty", "letmein",
            "Str0ngPassw0rd!", "iloveyou", "admin", "welcome"
        ]

        brute = bruteforce_storage(
            user=weak_user,
            correct_password=weak_pw,
            text_obj=weak_text,
            candidate_passwords=candidates,
        )

        metrics_rows.append({
            "category": "attack",
            "operation": "bruteforce_storage_dictionary",
            "username": weak_user.username,
            "size_bytes": getattr(weak_text, "content_size", ""),
            "avg_seconds": brute["bruteforce_seconds"],
            "notes": f"attempts={brute['bruteforce_attempts']} found={brute['bruteforce_found_password']} correct={brute['bruteforce_found_is_correct']}",
        })

        print("\n Bruteforce dictionary against encrypted storage for eval_weak")
        print(f"  attempts: {brute['bruteforce_attempts']}")
        print(f"  seconds:  {brute['bruteforce_seconds']:.6f}")
        print(f"  found:    {brute['bruteforce_found_password']}")
        print(f"  correct:  {brute['bruteforce_found_is_correct']}")

        # Save CSV results
        write_csv(CSV_PATH, metrics_rows)
        print(f"\n Wrote metrics CSV: {CSV_PATH}")

        print("\n Security implications")
        if brute["bruteforce_found_is_correct"]:
            print(f" {brute['bruteforce_attempts']} guesses.\n")
        else:
            print("The dictionary attack did not find the correct password within the tested list.\n")


if __name__ == "__main__":
    main()