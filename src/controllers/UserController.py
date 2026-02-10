from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import logout_user, login_required
from src.services.implementations.UserAuthServiceImplementation import UserAuthServiceImplementation


user_controller = Blueprint('user_controller', __name__, template_folder='templates')
auth = UserAuthServiceImplementation()

@user_controller.get("/logout")
@login_required
def logout():
    session.pop("master_key", None)
    logout_user()
    flash("Logged out successfully")
    return redirect(url_for("home_controller.index"))