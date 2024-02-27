# pylint: disable=broad-exception-raised,broad-exception-caught
"""
A test flask application that uses the ab_testing framework
"""

import uuid
from datetime import datetime
from enum import Enum

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from src.database.models import Experiment, FunnelStep, User
from src.interface import ExperimentInterface
from src.services import AuthService, ExperimentService, FunnelEventService
from src.shared import db

app = Flask(__name__)
app.secret_key = db.env["FLASK_SECRET_KEY"]


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


@app.route("/", methods=["GET", "POST"])
def index():
    """
    Home page
    """
    if not session_variables_set():
        create_session()

    if request.method == "POST":
        # This should match the name associated with participant, but
        # can be overridden by the query string

        button_value = request.form.get("red_vs_blue", "")
        print(f"Variant funnel advanced: {button_value}")
        return redirect(url_for("register"))

    if is_logged_in() or db.env["BUTTON_EXPERIMENT_UUID"] is None:
        return render_template(
            "index.html", logged_in=is_logged_in(), variant=RvBVariant()
        )

    override = request.args.get("r_v_b_override")
    if override is not None:
        print(f"Overriding variant to {override}")
        return render_template(
            "index.html", logged_in=is_logged_in(), variant=RvBVariant(override)
        )

    rb_experiment_uuid = uuid.UUID(db.env["BUTTON_EXPERIMENT_UUID"])
    rb_experiment: Experiment = ExperimentInterface.get_experiment(rb_experiment_uuid)

    if not rb_experiment:
        return render_template(
            "index.html", logged_in=is_logged_in(), variant=RvBVariant()
        )

    # Attempt to place the participant in an the button color+text experiment
    participant_uuid = session["session_uuid"]
    variant_name = ExperimentInterface.get_variant_name(
        rb_experiment_uuid, participant_uuid
    )

    return render_template(
        "index.html", logged_in=is_logged_in(), variant=RvBVariant(variant_name)
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Login page
    """
    if is_logged_in():
        return redirect(url_for("personal_page"))

    if request.method == "POST":
        if not session_variables_set():
            create_session()

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        current_user = AuthService.get_user_by_username(username)
        if current_user is None:
            return render_template(
                "login.html", error_message="Invalid credentials", logged_in=False
            )

        if not AuthService.validate_auth(current_user.user_uuid, username, password):
            return render_template(
                "login.html", error_message="Invalid credentials", logged_in=False
            )

        session["user_uuid"] = current_user.user_uuid
        session["session_step"] = FunnelStep.SIGNED_UP.value

        FunnelEventService.create_funnel_event(
            session["session_uuid"], FunnelStep.SIGNED_UP.value, datetime.now()
        )
        FunnelEventService.attempt_to_link_participant(
            session["session_uuid"], current_user.user_uuid
        )
        return redirect(url_for("personal_page"))

    return render_template("login.html", logged_in=False)


@app.route("/personal_page")
def personal_page():
    """
    Personal page
    """
    if not is_logged_in():
        return redirect(url_for("login"))

    user: User = AuthService.get_user(session["user_uuid"])
    return render_template("personal_page.html", logged_in=True, user=user)


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Register page
    """
    if is_logged_in():
        return redirect(url_for("personal_page"))

    if request.method == "POST":
        if not session_variables_set():
            create_session()

        username = request.form.get("username", "")
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if password != confirm:
            return render_template(
                "register.html", error_message="Passwords do not match"
            )

        if AuthService.get_user_by_username(username) is not None:
            return render_template(
                "register.html", error_message="Username already taken"
            )

        try:
            user = AuthService.create_user(username, password)
        except Exception as e:
            if "Password" in str(e):
                message = "Invalid password. Rules: ..."
            else:
                message = "Invalid username. Rules: ..."

            return render_template("register.html", error_message=message)

        session["user_uuid"] = user.user_uuid
        session["session_step"] = FunnelStep.SIGNED_UP.value
        FunnelEventService.create_funnel_event(
            session["session_uuid"], FunnelStep.SIGNED_UP.value, datetime.now()
        )
        return redirect(url_for("personal_page"))

    if not session_variables_set():
        create_session()

    session["session_step"] = FunnelStep.SIGNING_UP.value
    FunnelEventService.create_funnel_event(
        session["session_uuid"], FunnelStep.SIGNING_UP.value, datetime.now()
    )
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

    FunnelEventService.create_funnel_event(
        session["session_uuid"], FunnelStep.LANDED.value, datetime.now()
    )


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


@app.route("/experiment/<experiment_uuid>", methods=["GET", "POST"])
def experiment_route(experiment_uuid):
    """
    List all experiments. This would be only visible to
    admins in a real application
    """
    if not is_logged_in():
        return redirect(url_for("login"))

    if not experiment_uuid:
        return render_template("experiments.html", logged_in=True)

    actual_uuid = uuid.UUID(experiment_uuid)

    if request.method == "POST":
        experiment_button = request.form.get("status-adv", "")
        update_allocations = request.form.getlist("allocation-value")
        previous_status = ExperimentService.get_experiment(
            actual_uuid
        ).experiment_status

        if experiment_button == "Play":
            new_status = ExperimentService.start_experiment(actual_uuid)
        elif experiment_button == "Pause":
            new_status = ExperimentService.pause_experiment(actual_uuid)
        elif experiment_button == "Stop":
            new_status = ExperimentService.stop_experiment(actual_uuid)
        elif experiment_button == "Complete":
            new_status = ExperimentService.complete_experiment(actual_uuid)
        else:
            new_status = previous_status

        message = f"Experiment: {previous_status.value} -> {new_status.value}."

        if update_allocations:
            float_allocations = [float(alloc) for alloc in update_allocations]
            allocated = ExperimentInterface.update_variant_allocations(
                actual_uuid, float_allocations
            )
            if not allocated:
                message += "\nAllocation update failed"
            else:
                message += "\nAllocation updated"

        return render_template(
            "experiment.html",
            summary=ExperimentInterface.get_experiment_summary(actual_uuid),
            logged_in=True,
            message=message,
        )
    experiment_summary = ExperimentInterface.get_experiment_summary(
        uuid.UUID(experiment_uuid)
    )

    if not experiment_summary:
        return redirect(url_for("experiments_route"))

    return render_template(
        "experiment.html", summary=experiment_summary, logged_in=True
    )


@app.route("/experiments", methods=["GET", "POST"])
def experiments_route():
    """
    List all experiments. This would be only visible to
    admins in a real application
    """
    if not is_logged_in():
        return redirect(url_for("login"))

    all_experiments = ExperimentInterface.get_all_experiments()
    return render_template(
        "experiments.html", logged_in=True, experiments=all_experiments
    )
