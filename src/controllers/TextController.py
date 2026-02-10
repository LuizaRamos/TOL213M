import base64

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session
from flask_login import login_required, current_user
from src.persistences.models.Text import Text
from src.services.implementations.UserAuthServiceImplementation import UserAuthServiceImplementation
from src.services.implementations.TextServiceImplementaion import TextServiceImplementaion
from src.persistences.repositories.TextRepository import TextRepository

text_controller = Blueprint("text_controller", __name__, template_folder="templates")
auth = UserAuthServiceImplementation()

def require_login():
    if not current_user.is_authenticated:
        return None

    master_key = session.get("master_key")
    if not master_key:
        return None

    master_key = base64.b64decode(master_key)
    return current_user.id, master_key

@text_controller.get("/dashboard")
@login_required
def dashboard():
    ctx = require_login()
    if not ctx:
        return redirect(url_for("home_controller.index"))

    texts = Text.query.filter_by(user_id=current_user.id).order_by(Text.created_at.desc()).all()
    return render_template("dashboard.html", user=current_user, texts=texts)

@text_controller.get("/upload")
def upload_page():
    if not require_login():
        return redirect(url_for("home_controller.index"))
    return render_template("upload.html")

@text_controller.post("/upload")
def upload():
    ctx = require_login()
    if not ctx:
        return redirect(url_for("home_controller.index"))

    user_id, master_key = ctx

    title = request.form.get("title", "Untitled").strip()
    content = request.form.get("content", "")

    if not content:
        flash("Text content is required")
        return redirect(url_for("text_controller.upload"))

    service = TextServiceImplementaion(master_key)
    service.encrypt_and_store(user_id, title, content)

    flash("Encrypted text stored successfully.")
    return redirect(url_for("text_controller.dashboard"))

@text_controller.get("/text/<int:text_id>")
def view_text(text_id: int):
    ctx = require_login()
    if not ctx:
        return redirect(url_for("home_controller.index"))

    user_id, master_key = ctx
    text_obj = TextRepository.find_for_user(text_id, user_id)
    if not text_obj:
        abort(404)

    service = TextServiceImplementaion(master_key)
    plaintext = service.decrypt_for_user(text_obj)

    return render_template("upload.html", viewing=True, title=text_obj.title, content=plaintext)
