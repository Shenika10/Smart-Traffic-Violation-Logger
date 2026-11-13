from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import qrcode
import os

app = Flask(__name__)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///traffic_violations.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# Violation table
class Violation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), nullable=False)
    violation_type = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    fine_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="Unpaid")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/add-violation", methods=["GET", "POST"])
def add_violation():

    if request.method == "POST":

        vehicle_number = request.form["vehicle_number"]
        violation_type = request.form["violation_type"]
        location = request.form["location"]
        date = request.form["date"]
        fine_amount = request.form["fine_amount"]

        violation = Violation(
            vehicle_number=vehicle_number,
            violation_type=violation_type,
            location=location,
            date=date,
            fine_amount=fine_amount
        )

        db.session.add(violation)
        db.session.commit()

        qr_data = f"http://127.0.0.1:5000/violation/{violation.id}"

        qr = qrcode.make(qr_data)

        qr_folder = os.path.join("static", "qrcodes")
        os.makedirs(qr_folder, exist_ok=True)

        qr_path = os.path.join(
            qr_folder,
            f"violation_{violation.id}.png"
        )

        qr.save(qr_path)

        return render_template("success.html")

    return render_template("add_violation.html")


@app.route("/history")
def history():

    vehicle_number = request.args.get("vehicle_number")
    violation_type = request.args.get("violation_type")
    status = request.args.get("status")

    query = Violation.query


    if vehicle_number:
        query = query.filter_by(vehicle_number=vehicle_number)

    if violation_type:
        query = query.filter_by(violation_type=violation_type)

    if status:
        query = query.filter_by(status=status)
       
    violations = query.all()

    qr_folder = os.path.join("static", "qrcodes")
    os.makedirs(qr_folder, exist_ok=True)

    for violation in violations:

        qr_path = os.path.join(
            qr_folder,
            f"violation_{violation.id}.png"
        )

        if not os.path.exists(qr_path):

            qr_data = f"http://127.0.0.1:5000/violation/{violation.id}"

            qr = qrcode.make(qr_data)

            qr.save(qr_path)

    return render_template("history.html", violations=violations)


@app.route("/mark-paid/<int:violation_id>", methods=["POST"])
def mark_paid(violation_id):

    violation = Violation.query.get_or_404(violation_id)

    violation.status = "Paid"

    db.session.commit()

    return redirect("/history")


@app.route("/delete-violation/<int:violation_id>", methods=["POST"])
def delete_violation(violation_id):

    violation = Violation.query.get_or_404(violation_id)

    qr_path = os.path.join(
        "static",
        "qrcodes",
        f"violation_{violation.id}.png"
    )

    if os.path.exists(qr_path):
        os.remove(qr_path)

    db.session.delete(violation)
    db.session.commit()

    return redirect("/history")


@app.route("/violation/<int:violation_id>")
def view_violation(violation_id):

     violation = Violation.query.get_or_404(violation_id)

     return render_template(
         "violation.html",
         violation=violation
     )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)