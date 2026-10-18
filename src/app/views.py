from flask import Blueprint, abort, redirect, render_template, request, url_for

from ..db.cases import get_cases
from ..db.db import get_db
from ..models.filters import CaseFilters
from ..models.validation import validate_date

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    try:
        filters = CaseFilters.from_request(request)
    except ValueError as error:
        abort(400, description=str(error))

    cases = get_cases(filters)
    return render_template("index.html", cases=cases, filters=filters, q=filters.q)


def redirect_saved(anchor):
    """Подтвердить успешную запись черновику, если пришёл токен формы."""
    kwargs = {"_anchor": anchor}
    token = request.args.get("_draft", "")
    if token:
        kwargs["draft_saved"] = token
    return redirect(url_for("main.index", **kwargs), code=303)


def require_get():
    if request.method != "GET":
        abort(405)


def get_case_or_404(case_id):
    case = get_db().execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    if case is None:
        abort(404, description="Дело не найдено.")
    return case


def read_case_values(existing=None):
    defaults = dict(existing) if existing is not None else {
        "title": "", "description": "", "promised_on": "", "due_on": "", "status": "open",
    }
    values = {
        field: request.args.get(field, defaults[field]).strip()
        for field in ("title", "description", "promised_on", "due_on", "status")
    }
    if not values["title"]:
        abort(400, description="Название дела обязательно.")
    if values["status"] not in ("open", "closed"):
        abort(400, description="Неизвестный статус дела.")
    for field in ("promised_on", "due_on"):
        try:
            validate_date(values[field], field)
        except ValueError as error:
            abort(400, description=str(error))
    return values


def read_comment_body():
    body = request.args.get("body", "").strip()
    if not body:
        abort(400, description="Текст комментария обязателен.")
    return body


@bp.get("/cases/add")
def add_case():
    require_get()
    values = read_case_values()
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO cases (title, description, promised_on, due_on, status, closed_at) "
            "VALUES (:title, :description, :promised_on, :due_on, :status, "
            "CASE WHEN :status = 'closed' THEN strftime('%Y-%m-%dT%H:%M:%fZ', 'now') END)",
            values,
        )
    return redirect_saved(f"case-{cursor.lastrowid}")


@bp.get("/cases/<int:case_id>/edit")
def edit_case(case_id):
    require_get()
    values = read_case_values(get_case_or_404(case_id))
    values["id"] = case_id
    db = get_db()
    with db:
        db.execute(
            "UPDATE cases SET title = :title, description = :description, "
            "promised_on = :promised_on, due_on = :due_on, status = :status, "
            "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now'), "
            "closed_at = CASE WHEN :status = 'closed' "
            "THEN coalesce(closed_at, strftime('%Y-%m-%dT%H:%M:%fZ', 'now')) END "
            "WHERE id = :id",
            values,
        )
    return redirect_saved(f"case-{case_id}")


@bp.get("/cases/<int:case_id>/comments/add")
def add_comment(case_id):
    require_get()
    get_case_or_404(case_id)
    body = read_comment_body()
    db = get_db()
    with db:
        cursor = db.execute("INSERT INTO comments (case_id, body) VALUES (?, ?)", (case_id, body))
    return redirect_saved(f"comment-{cursor.lastrowid}")


@bp.get("/comments/<int:comment_id>/edit")
def edit_comment(comment_id):
    require_get()
    db = get_db()
    comment = db.execute("SELECT * FROM comments WHERE id = ?", (comment_id,)).fetchone()
    if comment is None:
        abort(404, description="Комментарий не найден.")
    body = read_comment_body()
    with db:
        db.execute("UPDATE comments SET body = ? WHERE id = ?", (body, comment_id))
    return redirect_saved(f"comment-{comment_id}")
