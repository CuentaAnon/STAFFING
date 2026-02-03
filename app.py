from __future__ import annotations

import os
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from db import Database
import matplotlib
matplotlib.use('Agg') # Evita que Matplotlib intente abrir una ventana


class CareerPlannerApp(ttk.Frame):
    def __init__(self, master: tk.Tk, db: Database) -> None:
        super().__init__(master)
        self.db = db
        self.scenario_id: int | None = None

        self._build_ui()
        self._refresh_scenarios()

    def _build_ui(self) -> None:
        self.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=12, pady=8)

        ttk.Label(
            header,
            text="Quarterly Scenarios (click a tab to switch between years/quarters)",
        ).pack(side=tk.LEFT)
        ttk.Button(header, text="Seed 5 Years (Quarterly)", command=self._seed_quarters).pack(
            side=tk.RIGHT
        )

        self.scenario_tabs = ttk.Notebook(self)
        self.scenario_tabs.pack(fill=tk.X, padx=12, pady=4)
        self.scenario_tabs.bind("<<NotebookTabChanged>>", self._on_scenario_tab_change)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        self.position_tab = ttk.Frame(self.notebook)
        self.chart_tab = ttk.Frame(self.notebook)
        self.employee_tab = ttk.Frame(self.notebook)
        self.assignment_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.position_tab, text="Positions")
        self.notebook.add(self.chart_tab, text="Org Chart")
        self.notebook.add(self.employee_tab, text="Employees")
        self.notebook.add(self.assignment_tab, text="Assignments")

        self._build_positions_tab()
        self._build_chart_tab()
        self._build_employees_tab()
        self._build_assignments_tab()

    def _seed_quarters(self) -> None:
        self.db.seed_quarter_scenarios(5)
        self._refresh_scenarios()

    def _refresh_scenarios(self) -> None:
        scenarios = self.db.list_scenarios()
        self.scenarios = scenarios
        self.scenario_tabs_tabs = {}
        for tab in self.scenario_tabs.tabs():
            self.scenario_tabs.forget(tab)
        for scenario in scenarios:
            frame = ttk.Frame(self.scenario_tabs)
            self.scenario_tabs.add(frame, text=scenario.name)
            self.scenario_tabs_tabs[frame] = scenario.id
        if scenarios:
            self.scenario_tabs.select(0)
            self.scenario_id = scenarios[0].id
            self._refresh_all()

    def _on_scenario_tab_change(self, _event: tk.Event) -> None:
        selected = self.scenario_tabs.select()
        frame = self.nametowidget(selected)
        self.scenario_id = self.scenario_tabs_tabs.get(frame)
        self._refresh_all()

    def _refresh_all(self) -> None:
        self._refresh_positions()
        self._refresh_chart()
        self._refresh_employees()
        self._refresh_assignments()

    def _build_positions_tab(self) -> None:
        form = ttk.LabelFrame(self.position_tab, text="Add Position")
        form.pack(fill=tk.X, padx=8, pady=8)

        self.position_title = tk.StringVar()
        self.position_department = tk.StringVar()
        self.position_parent = tk.StringVar()

        ttk.Label(form, text="Title").grid(row=0, column=0, sticky=tk.W, padx=4, pady=4)
        ttk.Entry(form, textvariable=self.position_title, width=30).grid(
            row=0, column=1, padx=4, pady=4
        )
        ttk.Label(form, text="Department").grid(row=0, column=2, sticky=tk.W, padx=4, pady=4)
        ttk.Entry(form, textvariable=self.position_department, width=24).grid(
            row=0, column=3, padx=4, pady=4
        )
        ttk.Label(form, text="Reports To (optional)").grid(
            row=1, column=0, sticky=tk.W, padx=4, pady=4
        )
        self.position_parent_combo = ttk.Combobox(form, textvariable=self.position_parent)
        self.position_parent_combo.grid(row=1, column=1, padx=4, pady=4)

        ttk.Button(form, text="Add", command=self._add_position).grid(
            row=1, column=3, sticky=tk.E, padx=4, pady=4
        )

        self.position_tree = ttk.Treeview(
            self.position_tab, columns=("dept", "parent"), show="headings", height=12
        )
        self.position_tree.heading("dept", text="Department")
        self.position_tree.heading("parent", text="Reports To")
        self.position_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        ttk.Button(self.position_tab, text="Delete Selected", command=self._delete_position).pack(
            padx=8, pady=8, anchor=tk.E
        )

    def _build_chart_tab(self) -> None:
        controls = ttk.Frame(self.chart_tab)
        controls.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(controls, text="Subchart Root").pack(side=tk.LEFT)
        self.chart_root = tk.StringVar(value="(Full Org Chart)")
        self.chart_root_combo = ttk.Combobox(controls, textvariable=self.chart_root, width=40)
        self.chart_root_combo.pack(side=tk.LEFT, padx=8)
        ttk.Button(controls, text="View", command=self._refresh_chart).pack(side=tk.LEFT)

        self.chart_tree = ttk.Treeview(self.chart_tab, show="tree", height=16)
        self.chart_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _build_employees_tab(self) -> None:
        form = ttk.LabelFrame(self.employee_tab, text="Add Employee")
        form.pack(fill=tk.X, padx=8, pady=8)

        self.employee_code = tk.StringVar()
        self.employee_name = tk.StringVar()

        ttk.Label(form, text="Employee Code").grid(row=0, column=0, sticky=tk.W, padx=4, pady=4)
        ttk.Entry(form, textvariable=self.employee_code, width=20).grid(
            row=0, column=1, padx=4, pady=4
        )
        ttk.Label(form, text="Full Name").grid(row=0, column=2, sticky=tk.W, padx=4, pady=4)
        ttk.Entry(form, textvariable=self.employee_name, width=30).grid(
            row=0, column=3, padx=4, pady=4
        )
        ttk.Button(form, text="Add", command=self._add_employee).grid(
            row=0, column=4, padx=4, pady=4
        )

        self.employee_tree = ttk.Treeview(
            self.employee_tab, columns=("code",), show="headings", height=12
        )
        self.employee_tree.heading("code", text="Employee Code")
        self.employee_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        ttk.Button(self.employee_tab, text="Delete Selected", command=self._delete_employee).pack(
            padx=8, pady=8, anchor=tk.E
        )

    def _build_assignments_tab(self) -> None:
        form = ttk.LabelFrame(self.assignment_tab, text="Move / Assign Employee")
        form.pack(fill=tk.X, padx=8, pady=8)

        self.assignment_employee = tk.StringVar()
        self.assignment_position = tk.StringVar()
        self.assignment_start = tk.StringVar(value=date.today().isoformat())

        ttk.Label(form, text="Employee").grid(row=0, column=0, sticky=tk.W, padx=4, pady=4)
        self.assignment_employee_combo = ttk.Combobox(form, textvariable=self.assignment_employee)
        self.assignment_employee_combo.grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(form, text="New Position").grid(row=0, column=2, sticky=tk.W, padx=4, pady=4)
        self.assignment_position_combo = ttk.Combobox(form, textvariable=self.assignment_position)
        self.assignment_position_combo.grid(row=0, column=3, padx=4, pady=4)

        ttk.Label(form, text="Start Date").grid(row=0, column=4, sticky=tk.W, padx=4, pady=4)
        ttk.Entry(form, textvariable=self.assignment_start, width=12).grid(
            row=0, column=5, padx=4, pady=4
        )

        ttk.Button(form, text="Save Move", command=self._move_employee).grid(
            row=0, column=6, padx=4, pady=4
        )

        self.assignment_tree = ttk.Treeview(
            self.assignment_tab,
            columns=("employee", "position", "start", "end"),
            show="headings",
            height=12,
        )
        self.assignment_tree.heading("employee", text="Employee")
        self.assignment_tree.heading("position", text="Position")
        self.assignment_tree.heading("start", text="Start Date")
        self.assignment_tree.heading("end", text="End Date")
        self.assignment_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        ttk.Button(
            self.assignment_tab, text="Delete Selected", command=self._delete_assignment
        ).pack(padx=8, pady=8, anchor=tk.E)

    def _add_position(self) -> None:
        if self.scenario_id is None:
            messagebox.showwarning("Missing scenario", "Please select a scenario first.")
            return
        title = self.position_title.get().strip()
        department = self.position_department.get().strip()
        if not title or not department:
            messagebox.showwarning("Missing data", "Title and department are required.")
            return
        parent_id = self._combo_value_to_id(self.position_parent.get(), self._positions_cache)
        self.db.add_position(self.scenario_id, title, department, parent_id)
        self.position_title.set("")
        self.position_department.set("")
        self.position_parent.set("")
        self._refresh_positions()

    def _add_employee(self) -> None:
        code = self.employee_code.get().strip()
        name = self.employee_name.get().strip()
        if not code or not name:
            messagebox.showwarning("Missing data", "Employee code and full name are required.")
            return
        try:
            self.db.add_employee(code, name)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", f"Unable to add employee: {exc}")
            return
        self.employee_code.set("")
        self.employee_name.set("")
        self._refresh_employees()

    def _move_employee(self) -> None:
        if self.scenario_id is None:
            messagebox.showwarning("Missing scenario", "Please select a scenario first.")
            return
        employee_id = self._combo_value_to_id(
            self.assignment_employee.get(), self._employees_cache
        )
        position_id = self._combo_value_to_id(
            self.assignment_position.get(), self._positions_cache
        )
        start_date = self.assignment_start.get().strip()
        if not employee_id or not position_id or not start_date:
            messagebox.showwarning("Missing data", "Employee, position, and start date are required.")
            return
        self.db.move_employee(employee_id, position_id, start_date)
        self._refresh_assignments()

    def _delete_position(self) -> None:
        selected = self.position_tree.selection()
        if not selected:
            return
        position_id = int(selected[0])
        self.db.delete_position(position_id)
        self._refresh_positions()

    def _delete_employee(self) -> None:
        selected = self.employee_tree.selection()
        if not selected:
            return
        employee_id = int(selected[0])
        self.db.delete_employee(employee_id)
        self._refresh_employees()

    def _delete_assignment(self) -> None:
        selected = self.assignment_tree.selection()
        if not selected:
            return
        assignment_id = int(selected[0])
        self.db.delete_assignment(assignment_id)
        self._refresh_assignments()

    def _refresh_positions(self) -> None:
        if self.scenario_id is None:
            return
        self.position_tree.delete(*self.position_tree.get_children())
        positions = self.db.list_positions(self.scenario_id)
        self._positions_cache = {position.title: position.id for position in positions}
        for position in positions:
            parent_name = next(
                (p.title for p in positions if p.id == position.parent_position_id),
                "",
            )
            self.position_tree.insert(
                "",
                tk.END,
                iid=str(position.id),
                values=(position.department, parent_name),
                text=position.title,
            )
        self.position_tree.configure(displaycolumns=("dept", "parent"))
        self.position_tree["show"] = ("tree", "headings")
        self.position_tree.heading("#0", text="Title")
        self.position_parent_combo["values"] = [position.title for position in positions]
        self.assignment_position_combo["values"] = [position.title for position in positions]
        self.chart_root_combo["values"] = ["(Full Org Chart)"] + [
            position.title for position in positions
        ]
        if not self.chart_root.get():
            self.chart_root.set("(Full Org Chart)")

    def _refresh_employees(self) -> None:
        self.employee_tree.delete(*self.employee_tree.get_children())
        employees = self.db.list_employees()
        self._employees_cache = {employee.full_name: employee.id for employee in employees}
        for employee in employees:
            self.employee_tree.insert(
                "",
                tk.END,
                iid=str(employee.id),
                values=(employee.employee_code,),
                text=employee.full_name,
            )
        self.employee_tree.configure(displaycolumns=("code",))
        self.employee_tree["show"] = ("tree", "headings")
        self.employee_tree.heading("#0", text="Employee")
        self.assignment_employee_combo["values"] = [employee.full_name for employee in employees]

    def _refresh_assignments(self) -> None:
        if self.scenario_id is None:
            return
        self.assignment_tree.delete(*self.assignment_tree.get_children())
        assignments = self.db.list_assignments(self.scenario_id)
        employees = {employee.id: employee.full_name for employee in self.db.list_employees()}
        positions = {position.id: position.title for position in self.db.list_positions(self.scenario_id)}
        for assignment in assignments:
            self.assignment_tree.insert(
                "",
                tk.END,
                iid=str(assignment.id),
                values=(
                    employees.get(assignment.employee_id, ""),
                    positions.get(assignment.position_id, ""),
                    assignment.start_date,
                    assignment.end_date or "",
                ),
            )

    def _refresh_chart(self) -> None:
        if self.scenario_id is None:
            return
        self.chart_tree.delete(*self.chart_tree.get_children())
        positions = self.db.list_positions(self.scenario_id)
        if not positions:
            return
        position_by_id = {position.id: position for position in positions}
        children: dict[int | None, list[int]] = {}
        for position in positions:
            children.setdefault(position.parent_position_id, []).append(position.id)
        for child_ids in children.values():
            child_ids.sort(
                key=lambda pid: (position_by_id[pid].department, position_by_id[pid].title)
            )

        root_selection = self.chart_root.get().strip()
        if root_selection and root_selection != "(Full Org Chart)":
            root_id = self._positions_cache.get(root_selection)
            if root_id is None:
                return
            self._insert_chart_node(root_id, "", position_by_id, children)
        else:
            for root_id in children.get(None, []):
                self._insert_chart_node(root_id, "", position_by_id, children)

    def _insert_chart_node(
        self,
        node_id: int,
        parent_item: str,
        position_by_id: dict[int, "Position"],
        children: dict[int | None, list[int]],
    ) -> None:
        position = position_by_id[node_id]
        label = f"{position.title} ({position.department})"
        item = self.chart_tree.insert(parent_item, tk.END, text=label)
        for child_id in children.get(node_id, []):
            self._insert_chart_node(child_id, item, position_by_id, children)

    @staticmethod
    def _combo_value_to_id(value: str, mapping: dict[str, int]) -> int | None:
        value = value.strip()
        if not value:
            return None
        return mapping.get(value)


def main() -> None:
    db = Database()
    db.seed_quarter_scenarios(5)

    if os.name != "nt" and not os.environ.get("DISPLAY"):
        raise SystemExit(
            "GUI launch failed: no display detected. "
            "Run on a machine with a graphical display or set $DISPLAY."
        )

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        raise SystemExit(f"GUI launch failed: {exc}") from exc
    root.title("Career Planning Database")
    root.geometry("980x720")

    style = ttk.Style(root)
    style.theme_use("clam")

    app = CareerPlannerApp(root, db)
    app.mainloop()


if __name__ == "__main__":
    main()
