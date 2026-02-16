import random
import sys
from pathlib import Path
from typing import List

from src.app import create_app
from src.persistences.models import db
from src.persistences.models.User import User
from src.persistences.models.Text import Text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

app = create_app()

AUTH_REPEATS = 20
CRYPTO_REPEATS = 10

RESULTS_DIR = PROJECT_ROOT / "evaluation"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

users_spec = [
    {"username": "eval_strong", "email": "eval_strong@example.com", "password": "Str0ngPassw0rd!"},
    {"username": "eval_weak", "email": "eval_weak@example.com", "password": "Password123"},
    {"username": "populating0", "email": "p0@example.com", "password": "jHydm96O"},
    {"username": "populating1", "email": "p1@example.com", "password": "RgksoP30"},
    {"username": "populating2", "email": "p2@example.com", "password": "!Kjfnie08"},
]

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

with app.app_context():
    for spec in users_spec:
        if not User.query.filter_by(username=spec["username"]).first():

            new_user = User(
                username = spec["username"],
                email = spec["email"]
            )

            new_user.set_password(spec["password"])

            db.session.add(new_user)
            db.session.flush()

            # Add a sample text for each user
            sample_text = Text(
                content=f"Hello, I am {spec['username']}!",
                user_id=new_user.id
            )
            db.session.add(sample_text)
            print(f"Added user: {spec['username']}")

        else:
            print(f"User {spec['username']} already exists. Skipping.")

        db.session.commit()
        print("Database seeded successfully using hashed password!")
