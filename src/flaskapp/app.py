# pylint: disable=broad-exception-raised
"""
A test flask application that uses the ab_testing framework
"""

import uuid
from enum import Enum

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from src.interface import ExperimentInterface
from src.services import AuthService
from src.shared import db

app = Flask(__name__)
app.secret_key = db.env["FLASK_SECRET_KEY"]


class FunnelStep(Enum):
    """
    Steps in the user 'funnel', how far along the user is
    """

    LANDED = "landed"
    SIGNING_UP = "signing_up"
    SIGNED_UP = "signed_up"

class RvBVariant:
    """
    A wrapper passed to jinja for displaying a modified button
    """

    def __init__(self, variant_name: str = "default"):
        self.variant_name = variant_name

    def get_color(self) -> str:
        """
        Get the color of the button
        """
        if "red" in self.variant_name:
            return "red"
        if "blue" in self.variant_name:
            return "blue"
        
        return "default"
    
    def get_text(self) -> str:
        """
        Get the text of the button
        """
        if "with_text" in self.variant_name:
            return "Start your journey!"
        
        return "Register"


@app.route("/")
def index():
    """
    Home page
    """
    if not session_variables_set():
        create_session()

    if is_logged_in() or db.env["BUTTON_EXPERIMENT_UUID"] is None:
        return render_template("index.html", logged_in=True, variant=RvBVariant())

    override = request.args.get("r_v_b_override")
    if override is not None:
        print(f"Overriding variant to {override}")
        return render_template("index.html", logged_in=is_logged_in(), variant=RvBVariant(override))
        
    # Attempt to place the participant in an the button color+text experiment
    rb_experiment_uuid = uuid.UUID(db.env["BUTTON_EXPERIMENT_UUID"])
    participant_uuid = session["session_uuid"]

    variant_name = ExperimentInterface.get_variant_name(
        rb_experiment_uuid,
        participant_uuid
    )

    return render_template("index.html", logged_in=is_logged_in(), variant=RvBVariant(variant_name))

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Login page
    """
    if is_logged_in():
        return redirect(url_for("personal_page"))

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        current_user = AuthService.get_user_by_username(username)
        if current_user is None:
            return render_template("login.html", error_message="Invalid credentials", logged_in=False)

        if not AuthService.validate_auth(current_user.user_uuid, username, password):
            return render_template("login.html", error_message="Invalid credentials", logged_in=False)

        session["user_uuid"] = current_user.user_uuid
        return redirect(url_for("personal_page"))

    return render_template("login.html", logged_in=False)


@app.route("/personal_page")
def personal_page():
    """
    Personal page
    """
    if not is_logged_in():
        return redirect(url_for("login"))

    return render_template("personal_page.html", loggeded_in=True)


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Register page
    """
    if is_logged_in():
        return redirect(url_for("personal_page"))

    if request.method == "POST":
        if not session_variables_set():
            raise Exception("Session variables not set")

        session["session_step"] = FunnelStep.SIGNED_UP.value
        return redirect(url_for("personal_page"))

    if not session_variables_set():
        create_session()

    session["session_step"] = FunnelStep.SIGNING_UP.value
    return render_template("register.html")


@app.route("/logout")
def logout():
    """
    Logout page
    """
    session.clear()
    return redirect(url_for("index"))


def create_session():
    """
    Create a new session
    """
    if "session_uuid" not in session:
        session["session_uuid"] = uuid.uuid4()
    session["session_step"] = FunnelStep.LANDED.value


def session_variables_set() -> bool:
    """
    Check if the session variables are set
    """
    return "session_uuid" in session and "session_step" in session


def is_logged_in() -> bool:
    """
    Check if the user is logged in
    """
    return "user_uuid" in session
