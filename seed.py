from __future__ import annotations
import sys
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.app import create_app
from src.persistences.models import db
from src.persistences.models.User import User
from src.services.implementations.TextServiceImplementation import TextServiceImplementation
from evaluation.evaluation import derive_master_key, load_text, make_text_of_exact_size

# Constants
TEXT_SIZES = [1_024, 10_240, 102_400, 1_048_576]  # 1KB, 10KB, 100KB, 1MB
RANDOM_SEED = 7278
TEXT_DIR = PROJECT_ROOT / "evaluation" / "texts"

text_source = load_text(TEXT_DIR)
rng = random.Random(RANDOM_SEED)

users_spec = [
    {"username": "eval_strong", "email": "eval_strong@example.com", "password": "Str0ngPassw0rd!"},
    {"username": "eval_weak", "email": "eval_weak@example.com", "password": "Password123"},
    {"username": "populating0", "email": "p0@example.com", "password": "jHydm96O"},
    {"username": "populating1", "email": "p1@example.com", "password": "RgksoP30"},
    {"username": "populating2", "email": "p2@example.com", "password": "!Kjfnie08"},
]

app = create_app()

with app.app_context():
    db.create_all()

    for spec in users_spec:

        u = User.query.filter_by(email=spec["email"]).first()

        if not u:
            u = User(username = spec["username"], email = spec["email"])
            u.set_password(spec["password"])
            db.session.add(u)
            db.session.flush() # ID is created here

            master_key = derive_master_key(spec["password"], u.kdf_salt)
            service = TextServiceImplementation(master_key)

            # Add a sample text for each user
            for size in TEXT_SIZES:
                plaintext = make_text_of_exact_size(size, text_source, rng)
                size_bytes = len(plaintext.encode("utf-8"))
                text_obj = service.encrypt_and_store(
                    user_id=u.id,
                    title=f"{u.username}_{size_bytes}B_one",
                    plaintext=plaintext
                )

            db.session.commit()

    print("Database populated.")