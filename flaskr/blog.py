from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)

from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint("blog", __name__)


@bp.route("/")
def index():
    db = get_db()

    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()

    return render_template('blog/index.html', posts=posts)


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required"
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


def get_post(id, check_author=True):
    db = get_db()
    post = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist")

    if check_author and post["author_id"] != g.user["id"]:
        abort(403)

    return post


def get_like_status_and_count(post_id, user_id=None):
    db = get_db()
    get_like_status = "SELECT status FROM like WHERE user_id = ? AND post_id = ?"
    get_like_count = "SELECT count(id) FROM like WHERE post_id = ? AND status = 1"
    like_count = db.execute(get_like_count, (post_id,)).fetchone()
    like_count = like_count["count(id)"]
    if user_id:
        """
        如果该用户第一次阅读一篇文章时，因为数据库中没有点赞记录，所以在执行get_like_status语句时，需要判断
        结果是否时None，如果是None，则表明数据库中没有该用户点赞或取消点赞的记录
        """
        like_status = db.execute(get_like_status, (user_id, post_id)).fetchone()
        if like_status is not None:
            return {
                "isLike": like_status["status"],
                "like_count": like_count
            }
        return {
            "isLike": "",
            "like_count": like_count
        }
    else:
        return {
            "isLike": "",
            "like_count": like_count
        }


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    post = get_post(id)

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required!"

        if error is not None:
            flash(error)

        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()

            return redirect(url_for("blog.index"))

    return render_template("blog/update.html", post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))


@bp.route("/post/<int:id>")
def post_detail(id):
    """
    获取某一篇文章
    :param id 文章id
    """
    post_ = get_post(id, False)
    if g.user:
        like_info = get_like_status_and_count(post_id=id, user_id=g.user["id"])
    else:
        like_info = get_like_status_and_count(post_id=id)
    return render_template("blog/post_detail.html", post=post_, like_info=like_info)


@bp.route("/post/like", methods=("POST",))
@login_required
def do_like():
    """
    用户点赞的实现
    因为使用login_required装饰器装饰，所以对于该视图的的请求，
    可以从全局变量G中获取user
    """
    db = get_db()
    if request.is_json:
        article_id = request.json.get("id")
        type_ = request.json.get("type")  # type=1 => 点赞，type=0 => 取消点赞
        if article_id is not None and type_ is not None:
            get_post(id=article_id, check_author=False)  # 先检查存不存在改id的文章，如果有才进行点赞
            if type_ not in (0, 1):
                return jsonify(errCode=3, errMessage="type值只能是0或1", msg="")
            user_id = g.user["id"]
            # 检查改点赞信息是否存在于数据库中，不存在则INSERT,否则获取id,以便更新
            insert_like_history = "INSERT INTO like (user_id, post_id, status) VALUES (?, ?, ?)"
            check_like_history = "SELECT id FROM like WHERE user_id = ? AND post_id = ?"
            update_like_status = "UPDATE like SET status = ? WHERE id = ?"
            get_like_count = "SELECT count(id) FROM like WHERE post_id = ? AND status = 1"
            like_history = db.execute(check_like_history, (user_id, article_id)).fetchone()
            # 存在数据库当中，更新status
            if like_history:
                db.execute(update_like_status, (type_, like_history["id"]))
                db.commit()
            else:
                # 不存在，则新创建
                db.execute(insert_like_history, (user_id, article_id, type_))
                db.commit()
            msg = "点赞成功" if type_ else "点赞取消成功"
            like_count = db.execute(get_like_count, (article_id,)).fetchone()["count(id)"]
            return jsonify(errCode=0, errMessage='', msg=msg, count=like_count)
        else:
            return jsonify(errCode=2, errMessage="请求数据无效", msg="")
    else:
        return jsonify(errCode=1, errMessage="请求数据格式错误", msg="")
