from functools import wraps

from flask import (
    Blueprint,flash,g,redirect,render_template,request,session,url_for
)

from werkzeug.security import check_password_hash,generate_password_hash

from flaskr.db import get_db

bp = Blueprint("auth",__name__,url_prefix="/auth")


# 注册
@bp.route("/register",methods=("GET","POST"))
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()  # 获取数据库连接
        error = None

        if not username:
            error = "Username is required"
        elif not password:
            error = "Password id required"
        elif db.execute("SELECT id FROM user WHERE username = ?",(username,)).fetchone() is not None:
            error = f"User {username} is already registed"

        if error is None:
            db.execute(
                "INSERT INTO user (username, password) VALUES (?,?)",(username,generate_password_hash(password))
            )
            db.commit()
            return redirect(url_for("auth.login"))
        flash(error)

    return render_template("auth/register.html")


# 登录
@bp.route("/login",methods=("GET","POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()  # 获取数据库连接
        error = None
        user = db.execute(
            "SELECT id,username,password FROM user WHERE username = ?",(username,)
        ).fetchone()

        if user is None:
            error = "Incorrect username"
        elif not check_password_hash(user["password"],password):
            error = "Incorrect password"

        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("index"))

        flash(error)

    return render_template("auth/login.html")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        db = get_db()
        g.user = db.execute(
            "SELECT id,username,password FROM user WHERE id = ?",(user_id,)
        ).fetchone()


# 注销
@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# 在其他视图中验证
def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped_view