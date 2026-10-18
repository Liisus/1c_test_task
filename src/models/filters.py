from __future__ import annotations

from dataclasses import dataclass

from flask import Request

from .validation import validate_date


@dataclass(frozen=True)
class CaseFilters:
    _Q_TITLE = "title LIKE ?"
    _Q_DESC = "description LIKE ?"
    _STATUS = "status = ?"
    _PROMISED_FROM = "promised_on >= ?"
    _PROMISED_TO = "promised_on <= ?"
    _DUE_FROM = "due_on >= ?"
    _DUE_TO = "due_on <= ?"

    status: str | None = None
    promised_from: str | None = None
    promised_to: str | None = None
    due_from: str | None = None
    due_to: str | None = None
    q: str = ""

    def _active_filters(self) -> list[tuple[str, str]]:
        search = f"%{self.q}%" if self.q else None
        return [
            (condition, value)
            for condition, value in (
                (self._Q_TITLE, search),
                (self._Q_DESC, search),
                (self._STATUS, self.status),
                (self._PROMISED_FROM, self.promised_from),
                (self._PROMISED_TO, self.promised_to),
                (self._DUE_FROM, self.due_from),
                (self._DUE_TO, self.due_to),
            )
            if value
        ]

    def get_conditions(self) -> list[str]:
        conditions = [condition for condition, _ in self._active_filters()]
        if self.q:

            conditions[:2] = ["(" + " OR ".join(conditions[:2]) + ")"]
        return conditions

    def get_parameters(self) -> list[str]:
        return [value for _, value in self._active_filters()]

    @staticmethod
    def from_request(request: Request) -> CaseFilters:
        q = request.args.get("q", "").strip()

        if any(char in "%_\\" or not char.isprintable() for char in q):
            raise ValueError("Поиск не допускает %, _, обратный слеш и управляющие символы.")

        status = request.args.get("status", "").strip() or None
        if status not in (None, "open", "closed"):
            raise ValueError("Неизвестный статус дела.")

        def read_date(name: str) -> str | None:
            value = request.args.get(name, "").strip()
            if not value:
                return None
            return validate_date(value, name)

        return CaseFilters(
            q=q,
            status=status,
            promised_from=read_date("promised_from"),
            promised_to=read_date("promised_to"),
            due_from=read_date("due_from"),
            due_to=read_date("due_to"),
        )
