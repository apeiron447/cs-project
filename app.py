from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for flash messages

# Demo login credentials
USER_CREDENTIALS = {
    "agnimithratheyyeth@gmail.com": "agnimithra230507",
    "admin": "adminpass"
}

# ------------------------
# LOGIN PAGE
# ------------------------
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email_or_id = request.form.get("email_or_id", "").strip()
        password = request.form.get("password", "").strip()

        if email_or_id in USER_CREDENTIALS and USER_CREDENTIALS[email_or_id] == password:
            flash("Login successful!", "success")
            return redirect(url_for("roles"))
        else:
            flash("Invalid Email/ID or Password.", "error")

    return render_template("login.html")


# ------------------------
# ROLES PAGE
# ------------------------
@app.route("/roles")
def roles():
    return render_template("roles.html")


# ------------------------
# SUPPORT PAGE
# ------------------------
@app.route("/support")
def support():
    return render_template("support.html")


# ------------------------
# ROLE FORMS
# ------------------------
@app.route("/department")
def department_form():
    return render_template("department.html")

@app.route("/course")
def course_form():
    return render_template("course.html")

@app.route("/student")
def student_form():
    return render_template("student.html")

@app.route("/teacher")
def teacher_form():
    return render_template("teacher.html")

# ------------------------
# PROGRAMME FORM PAGE
# ------------------------
@app.route("/programme", methods=["GET", "POST"])
def programme_form():
    if request.method == "POST":
        department = request.form.get("department")
        programme_name = request.form.get("programme_name")

        # Here you can save to the database
        print("Programme Saved:", department, programme_name)

        flash(f"Programme '{programme_name}' added successfully!", "success")
        return redirect(url_for("programme_form"))

    return render_template("programme.html")


@app.route("/semester")
def semester_form():
    return render_template("semester.html")


# ------------------------
# ADD BATCH PAGE
# ------------------------
@app.route("/add_batch")
def add_batch_form():
    return render_template("add_batch.html")   # MUST exist in templates/


# ------------------------
# SAVE BATCH FORM (POST)
# ------------------------
@app.route("/save_batch", methods=["POST"])
def save_batch():
    programme = request.form.get("programme")
    start_year = request.form.get("start_year")
    end_year = request.form.get("end_year")
    semester = request.form.get("semester")

    print("Batch Saved:", programme, start_year, end_year, semester)

    flash("Batch Created Successfully!", "success")
    return redirect(url_for("add_batch_form"))


# ------------------------
# RUN APP
# ------------------------
if __name__ == "__main__":
    app.run(debug=True)










