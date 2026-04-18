from datetime import date
from functools import wraps
import os

from flask import Flask, flash, redirect, render_template, request, session, url_for

from db import close_db, execute, get_db, query


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fittrack-dev-secret")
app.teardown_appcontext(close_db)


def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if "username" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("You do not have permission to view that page.")
                return redirect(url_for("login"))
            return view(**kwargs)

        return wrapped_view

    return decorator


def current_member():
    return query(
        "SELECT * FROM member WHERE username = %s",
        (session.get("username"),),
        one=True,
    )


def current_trainer():
    return query(
        "SELECT * FROM trainer WHERE username = %s",
        (session.get("username"),),
        one=True,
    )


def update_booking_status(booking_id, status, fine_amount):
    old = query(
        "SELECT member_id, status, fine_amount FROM trainer_booking WHERE booking_id = %s",
        (booking_id,),
        one=True,
    )
    if not old:
        return

    fine_amount = float(fine_amount or 0) if status == "missed" else 0
    execute(
        "UPDATE trainer_booking SET status = %s, fine_amount = %s WHERE booking_id = %s",
        (status, fine_amount, booking_id),
    )

    # Keep member.fine as the current total outstanding fine from missed sessions.
    execute(
        """
        UPDATE member
        SET fine = (
            SELECT COALESCE(SUM(fine_amount), 0)
            FROM trainer_booking
            WHERE member_id = %s AND status = 'missed'
        )
        WHERE member_id = %s
        """,
        (old["member_id"], old["member_id"]),
    )


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form["role"]
        username = request.form["username"]
        password = request.form["password"]
        user = query(
            "SELECT * FROM users WHERE username = %s AND password = %s AND role = %s",
            (username, password, role),
            one=True,
        )
        if user:
            session.clear()
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for(f"{role}_dashboard"))
        flash("Invalid login details.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/admin")
@login_required("admin")
def admin_dashboard():
    stats = {
        "members": query("SELECT COUNT(*) AS total FROM member", one=True)["total"],
        "trainers": query("SELECT COUNT(*) AS total FROM trainer", one=True)["total"],
        "bookings": query("SELECT COUNT(*) AS total FROM trainer_booking", one=True)["total"],
        "fines": query("SELECT COALESCE(SUM(fine), 0) AS total FROM member", one=True)["total"],
    }
    bookings = query(
        """
        SELECT tb.*, m.name AS member_name, t.name AS trainer_name, ts.start_time, ts.end_time
        FROM trainer_booking tb
        JOIN member m ON tb.member_id = m.member_id
        JOIN trainer t ON tb.trainer_id = t.trainer_id
        JOIN trainer_slot ts ON tb.slot_id = ts.slot_id
        ORDER BY tb.booking_date DESC, ts.start_time
        LIMIT 10
        """
    )
    return render_template("admin/dashboard.html", stats=stats, bookings=bookings)


@app.route("/admin/plans", methods=["GET", "POST"])
@login_required("admin")
def admin_plans():
    if request.method == "POST":
        execute(
            "INSERT INTO plans (plan_name, plan_price) VALUES (%s, %s)",
            (request.form["plan_name"], request.form["plan_price"]),
        )
        flash("Plan added.")
        return redirect(url_for("admin_plans"))
    plans = query("SELECT * FROM plans ORDER BY plan_id")
    return render_template("admin/plans.html", plans=plans)


@app.route("/admin/members", methods=["GET", "POST"])
@login_required("admin")
def admin_members():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, 'member')",
            (username, password),
        )
        execute(
            """
            INSERT INTO member
            (username, name, gender, dob, join_date, email, plan_id, daily_calorie_limit, expected_workout_minutes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                username,
                request.form["name"],
                request.form["gender"],
                request.form["dob"],
                request.form["join_date"],
                request.form["email"],
                request.form["plan_id"],
                request.form["daily_calorie_limit"],
                request.form["expected_workout_minutes"],
            ),
        )
        flash("Member added with login credentials.")
        return redirect(url_for("admin_members"))

    members = query(
        """
        SELECT m.*, p.plan_name
        FROM member m
        LEFT JOIN plans p ON m.plan_id = p.plan_id
        ORDER BY m.member_id
        """
    )
    plans = query("SELECT * FROM plans ORDER BY plan_name")
    return render_template("admin/members.html", members=members, plans=plans)


@app.route("/admin/trainers", methods=["GET", "POST"])
@login_required("admin")
def admin_trainers():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, 'trainer')",
            (username, password),
        )
        execute(
            """
            INSERT INTO trainer (username, name, gender, dob, specialization, experience)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                username,
                request.form["name"],
                request.form["gender"],
                request.form["dob"],
                request.form["specialization"],
                request.form["experience"],
            ),
        )
        flash("Trainer added with login credentials.")
        return redirect(url_for("admin_trainers"))

    trainers = query(
        """
        SELECT *, TIMESTAMPDIFF(YEAR, dob, CURDATE()) AS age
        FROM trainer
        ORDER BY trainer_id
        """
    )
    return render_template("admin/trainers.html", trainers=trainers)


@app.route("/admin/attendance", methods=["GET", "POST"])
@login_required("admin")
def admin_attendance():
    if request.method == "POST":
        execute(
            """
            INSERT INTO attendance (member_id, date, entry, exit_time)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE entry = VALUES(entry), exit_time = VALUES(exit_time)
            """,
            (
                request.form["member_id"],
                request.form["date"],
                request.form["entry"],
                request.form["exit_time"],
            ),
        )
        flash("Attendance saved.")
        return redirect(url_for("admin_attendance"))

    members = query("SELECT member_id, name FROM member ORDER BY name")
    attendance = query(
        """
        SELECT a.*, m.name
        FROM attendance a
        JOIN member m ON a.member_id = m.member_id
        ORDER BY a.date DESC, m.name
        LIMIT 50
        """
    )
    return render_template("admin/attendance.html", members=members, attendance=attendance)


@app.route("/admin/bookings", methods=["GET", "POST"])
@login_required("admin")
def admin_bookings():
    if request.method == "POST":
        update_booking_status(
            request.form["booking_id"],
            request.form["status"],
            request.form.get("fine_amount"),
        )
        flash("Booking status updated.")
        return redirect(url_for("admin_bookings"))

    bookings = query(
        """
        SELECT tb.*, m.name AS member_name, t.name AS trainer_name, ts.start_time, ts.end_time
        FROM trainer_booking tb
        JOIN member m ON tb.member_id = m.member_id
        JOIN trainer t ON tb.trainer_id = t.trainer_id
        JOIN trainer_slot ts ON tb.slot_id = ts.slot_id
        ORDER BY tb.booking_date DESC, ts.start_time
        """
    )
    return render_template("admin/bookings.html", bookings=bookings)


@app.route("/trainer")
@login_required("trainer")
def trainer_dashboard():
    trainer = current_trainer()
    bookings = query(
        """
        SELECT tb.*, m.name AS member_name, ts.start_time, ts.end_time
        FROM trainer_booking tb
        JOIN member m ON tb.member_id = m.member_id
        JOIN trainer_slot ts ON tb.slot_id = ts.slot_id
        WHERE tb.trainer_id = %s AND tb.booking_date = CURDATE()
        ORDER BY ts.start_time
        """,
        (trainer["trainer_id"],),
    )
    return render_template("trainer/dashboard.html", trainer=trainer, bookings=bookings)


@app.route("/trainer/bookings", methods=["GET", "POST"])
@login_required("trainer")
def trainer_bookings():
    trainer = current_trainer()
    if request.method == "POST":
        update_booking_status(
            request.form["booking_id"],
            request.form["status"],
            request.form.get("fine_amount"),
        )
        flash("Session status updated.")
        return redirect(url_for("trainer_bookings"))

    bookings = query(
        """
        SELECT tb.*, m.name AS member_name, ts.start_time, ts.end_time
        FROM trainer_booking tb
        JOIN member m ON tb.member_id = m.member_id
        JOIN trainer_slot ts ON tb.slot_id = ts.slot_id
        WHERE tb.trainer_id = %s
        ORDER BY tb.booking_date DESC, ts.start_time
        """,
        (trainer["trainer_id"],),
    )
    return render_template("trainer/bookings.html", bookings=bookings)


@app.route("/member")
@login_required("member")
def member_dashboard():
    member = current_member()
    attendance = query(
        """
        SELECT *,
               TIMESTAMPDIFF(MINUTE, entry, exit_time) AS workout_minutes
        FROM attendance
        WHERE member_id = %s
        ORDER BY date DESC
        LIMIT 1
        """,
        (member["member_id"],),
        one=True,
    )
    workout_minutes = attendance["workout_minutes"] if attendance and attendance["workout_minutes"] else 0
    difference = workout_minutes - member["expected_workout_minutes"]
    calorie_change = int(difference / 15) * 200
    dynamic_limit = max(0, member["daily_calorie_limit"] + calorie_change)
    total_calories = query(
        """
        SELECT COALESCE(SUM(calorie), 0) AS total
        FROM logs
        WHERE member_id = %s AND log_date = CURDATE()
        """,
        (member["member_id"],),
        one=True,
    )["total"]
    return render_template(
        "member/dashboard.html",
        member=member,
        attendance=attendance,
        workout_minutes=workout_minutes,
        dynamic_limit=dynamic_limit,
        calorie_change=calorie_change,
        total_calories=total_calories,
    )


@app.route("/member/trainers", methods=["GET", "POST"])
@login_required("member")
def member_trainers():
    member = current_member()
    if request.method == "POST":
        slot = query(
            "SELECT * FROM trainer_slot WHERE slot_id = %s",
            (request.form["slot_id"],),
            one=True,
        )
        if not slot:
            flash("Selected slot was not found.")
            return redirect(url_for("member_trainers"))
        try:
            execute(
                """
                INSERT INTO trainer_booking (member_id, trainer_id, slot_id, booking_date, status)
                VALUES (%s, %s, %s, %s, 'booked')
                """,
                (
                    member["member_id"],
                    slot["trainer_id"],
                    request.form["slot_id"],
                    request.form["booking_date"],
                ),
            )
            flash("Trainer session booked.")
        except Exception:
            get_db().rollback()
        flash("That trainer slot is already booked for the selected date.")
        return redirect(url_for("member_trainers"))

    selected_date = request.args.get("booking_date", date.today().isoformat())
    filters = {
        "specialization": request.args.get("specialization", ""),
        "experience": request.args.get("experience", ""),
        "age": request.args.get("age", ""),
        "gender": request.args.get("gender", ""),
    }
    sql = "SELECT *, TIMESTAMPDIFF(YEAR, dob, CURDATE()) AS age FROM trainer WHERE 1 = 1"
    params = []
    if filters["specialization"]:
        sql += " AND specialization LIKE %s"
        params.append(f"%{filters['specialization']}%")
    if filters["experience"]:
        sql += " AND experience >= %s"
        params.append(filters["experience"])
    if filters["age"]:
        sql += " AND TIMESTAMPDIFF(YEAR, dob, CURDATE()) <= %s"
        params.append(filters["age"])
    if filters["gender"]:
        sql += " AND gender = %s"
        params.append(filters["gender"])
    trainers = query(sql + " ORDER BY name", tuple(params))
    slots = query(
        """
        SELECT ts.*, t.name AS trainer_name
        FROM trainer_slot ts
        JOIN trainer t ON ts.trainer_id = t.trainer_id
        WHERE NOT EXISTS (
            SELECT 1
            FROM trainer_booking tb
            WHERE tb.trainer_id = ts.trainer_id
              AND tb.slot_id = ts.slot_id
              AND tb.booking_date = %s
        )
        ORDER BY t.name, ts.start_time
        """,
        (selected_date,),
    )
    return render_template(
        "member/trainers.html",
        trainers=trainers,
        slots=slots,
        filters=filters,
        selected_date=selected_date,
    )


@app.route("/member/private-room", methods=["GET", "POST"])
@login_required("member")
def private_room():
    member = current_member()
    if request.method == "POST":
        try:
            execute(
                """
                INSERT INTO private_booking (slot_id, member_id, booking_date)
                VALUES (%s, %s, %s)
                """,
                (request.form["slot_id"], member["member_id"], request.form["booking_date"]),
            )
            flash("Private room booked.")
        except Exception:
            get_db().rollback()
            flash("That private room slot is already booked for the selected date.")
        return redirect(url_for("private_room"))

    selected_date = request.args.get("booking_date", date.today().isoformat())
    slots = query(
        """
        SELECT *
        FROM private_slot ps
        WHERE NOT EXISTS (
            SELECT 1
            FROM private_booking pb
            WHERE pb.slot_id = ps.slot_id
              AND pb.booking_date = %s
        )
        ORDER BY start_time
        """,
        (selected_date,),
    )
    bookings = query(
        """
        SELECT pb.*, ps.start_time, ps.end_time
        FROM private_booking pb
        JOIN private_slot ps ON pb.slot_id = ps.slot_id
        WHERE pb.member_id = %s
        ORDER BY pb.booking_date DESC
        """,
        (member["member_id"],),
    )
    return render_template(
        "member/private_room.html",
        slots=slots,
        bookings=bookings,
        selected_date=selected_date,
    )


@app.route("/member/food", methods=["GET", "POST"])
@login_required("member")
def member_food():
    member = current_member()
    if request.method == "POST":
        food = query(
            "SELECT * FROM foodbank WHERE food = %s",
            (request.form["food"],),
            one=True,
        )
        if food:
            portion = float(request.form["portion"])
            execute(
                """
                INSERT INTO logs (food, member_id, calorie, log_date, portion)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    food["food"],
                    member["member_id"],
                    food["calorie"] * portion,
                    request.form["log_date"],
                    portion,
                ),
            )
            flash("Food log added.")
        return redirect(url_for("member_food"))

    foods = query("SELECT * FROM foodbank ORDER BY food")
    logs = query(
        """
        SELECT * FROM logs
        WHERE member_id = %s
        ORDER BY log_date DESC, log_id DESC
        """,
        (member["member_id"],),
    )
    totals = query(
        """
        SELECT log_date, SUM(calorie) AS total
        FROM logs
        WHERE member_id = %s
        GROUP BY log_date
        ORDER BY log_date DESC
        """,
        (member["member_id"],),
    )
    return render_template("member/food.html", foods=foods, logs=logs, totals=totals, today=date.today())


@app.route("/member/activity")
@login_required("member")
def member_activity():
    member = current_member()
    trainer_bookings = query(
        """
        SELECT tb.*, t.name AS trainer_name, ts.start_time, ts.end_time
        FROM trainer_booking tb
        JOIN trainer t ON tb.trainer_id = t.trainer_id
        JOIN trainer_slot ts ON tb.slot_id = ts.slot_id
        WHERE tb.member_id = %s
        ORDER BY tb.booking_date DESC
        """,
        (member["member_id"],),
    )
    attendance = query(
        """
        SELECT *, TIMESTAMPDIFF(MINUTE, entry, exit_time) AS workout_minutes
        FROM attendance
        WHERE member_id = %s
        ORDER BY date DESC
        """,
        (member["member_id"],),
    )
    food_logs = query(
        "SELECT * FROM logs WHERE member_id = %s ORDER BY log_date DESC",
        (member["member_id"],),
    )
    return render_template(
        "member/activity.html",
        member=member,
        trainer_bookings=trainer_bookings,
        attendance=attendance,
        food_logs=food_logs,
    )


if __name__ == "__main__":
    app.run(debug=True)
