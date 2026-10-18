from ..models.filters import CaseFilters
from .db import get_db


def get_cases(filters: CaseFilters) -> list[dict]:
    conditions = filters.get_conditions()
    parameters = filters.get_parameters()
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    db = get_db()
    query = "SELECT * FROM cases"
    query += where
    query += " ORDER BY due_on, id"
    cases = [dict(row) for row in db.execute(query, parameters).fetchall()]
    if not cases:
        return []

    comments = db.execute(
        "SELECT comments.* FROM comments JOIN cases ON cases.id = comments.case_id"
        + where
        + " ORDER BY comments.created_at, comments.id",
        parameters,
    ).fetchall()
    cases_by_id = {case["id"]: case for case in cases}
    for case in cases:
        case["comments"] = []
    for comment in comments:
        case = cases_by_id.get(comment["case_id"])
        if case is not None:
            case["comments"].append(dict(comment))

    return cases
