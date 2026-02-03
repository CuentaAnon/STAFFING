from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import date
from typing import Iterable

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "career_planning.db")


@dataclass(frozen=True)
class Scenario:
    id: int
    name: str
    year: int
    quarter: int
    start_date: str
    end_date: str


@dataclass(frozen=True)
class Position:
    id: int
    scenario_id: int
    title: str
    department: str
    parent_position_id: int | None


@dataclass(frozen=True)
class Employee:
    id: int
    employee_code: str
    full_name: str


@dataclass(frozen=True)
class Assignment:
    id: int
    employee_id: int
    position_id: int
    start_date: str
    end_date: str | None


class Database:
    def __init__(self, path: str = DB_PATH) -> None:
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._connect_and_init()

    def _connect_and_init(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS scenarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    quarter INTEGER NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    UNIQUE(year, quarter)
                );

                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scenario_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    department TEXT NOT NULL,
                    parent_position_id INTEGER,
                    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
                    FOREIGN KEY (parent_position_id) REFERENCES positions(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_code TEXT NOT NULL UNIQUE,
                    full_name TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    position_id INTEGER NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT,
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                    FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def seed_quarter_scenarios(self, years: int = 5) -> None:
        current_year = date.today().year
        scenarios = []
        for year in range(current_year, current_year + years):
            for quarter in range(1, 5):
                start_month = (quarter - 1) * 3 + 1
                start = date(year, start_month, 1)
                if start_month + 3 > 12:
                    end = date(year + 1, 1, 1)
                else:
                    end = date(year, start_month + 3, 1)
                end_date = end.replace(day=1)
                scenarios.append(
                    (
                        f"FY{year} Q{quarter}",
                        year,
                        quarter,
                        start.isoformat(),
                        end_date.isoformat(),
                    )
                )
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT OR IGNORE INTO scenarios (name, year, quarter, start_date, end_date)
                VALUES (?, ?, ?, ?, ?)
                """,
                scenarios,
            )

    def list_scenarios(self) -> list[Scenario]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, year, quarter, start_date, end_date FROM scenarios ORDER BY year, quarter"
            ).fetchall()
        return [Scenario(**row) for row in rows]

    def list_positions(self, scenario_id: int) -> list[Position]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, scenario_id, title, department, parent_position_id
                FROM positions
                WHERE scenario_id = ?
                ORDER BY department, title
                """,
                (scenario_id,),
            ).fetchall()
        return [Position(**row) for row in rows]

    def list_employees(self) -> list[Employee]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, employee_code, full_name FROM employees ORDER BY full_name"
            ).fetchall()
        return [Employee(**row) for row in rows]

    def list_assignments(self, scenario_id: int) -> list[Assignment]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT a.id, a.employee_id, a.position_id, a.start_date, a.end_date
                FROM assignments a
                JOIN positions p ON a.position_id = p.id
                WHERE p.scenario_id = ?
                ORDER BY a.start_date DESC
                """,
                (scenario_id,),
            ).fetchall()
        return [Assignment(**row) for row in rows]

    def add_position(
        self, scenario_id: int, title: str, department: str, parent_position_id: int | None
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO positions (scenario_id, title, department, parent_position_id)
                VALUES (?, ?, ?, ?)
                """,
                (scenario_id, title, department, parent_position_id),
            )

    def add_employee(self, employee_code: str, full_name: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO employees (employee_code, full_name) VALUES (?, ?)",
                (employee_code, full_name),
            )

    def add_assignment(
        self, employee_id: int, position_id: int, start_date: str, end_date: str | None
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO assignments (employee_id, position_id, start_date, end_date)
                VALUES (?, ?, ?, ?)
                """,
                (employee_id, position_id, start_date, end_date),
            )

    def move_employee(
        self, employee_id: int, new_position_id: int, start_date: str
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE assignments
                SET end_date = ?
                WHERE employee_id = ? AND end_date IS NULL
                """,
                (start_date, employee_id),
            )
            conn.execute(
                """
                INSERT INTO assignments (employee_id, position_id, start_date, end_date)
                VALUES (?, ?, ?, NULL)
                """,
                (employee_id, new_position_id, start_date),
            )

    def delete_position(self, position_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM positions WHERE id = ?", (position_id,))

    def delete_employee(self, employee_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM employees WHERE id = ?", (employee_id,))

    def delete_assignment(self, assignment_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))

    def bulk_positions(self, scenario_id: int) -> Iterable[tuple[int, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, title FROM positions WHERE scenario_id = ? ORDER BY title",
                (scenario_id,),
            ).fetchall()
        return [(row["id"], row["title"]) for row in rows]

    def bulk_employees(self) -> Iterable[tuple[int, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, full_name FROM employees ORDER BY full_name"
            ).fetchall()
        return [(row["id"], row["full_name"]) for row in rows]
