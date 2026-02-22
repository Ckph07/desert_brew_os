"""
Integration tests for Payroll Service — Employee, Payroll, and TipPool.
"""
import pytest


class TestEmployeeAPI:
    """Test employee CRUD endpoints."""

    def test_create_brewery_employee(self, client, sample_brewery_employee):
        """Test creating a brewery (PRODUCTION) fixed employee."""
        response = client.post("/api/v1/payroll/employees", json=sample_brewery_employee)
        assert response.status_code == 201
        data = response.json()
        assert data["full_name"] == "Miguel Ángel Rodríguez"
        assert data["employee_code"].startswith("EMP-")
        assert data["department"] == "PRODUCTION"
        assert data["employment_type"] == "FIXED"
        assert data["daily_salary"] == 833.33
        assert data["monthly_salary"] == 24999.90
        assert data["eligible_for_tips"] is False

    def test_create_taproom_fixed_employee(self, client, sample_taproom_employee):
        """Test creating a taproom fixed employee with tips and taxi."""
        response = client.post("/api/v1/payroll/employees", json=sample_taproom_employee)
        assert response.status_code == 201
        data = response.json()
        assert data["department"] == "TAPROOM"
        assert data["eligible_for_tips"] is True
        assert data["taxi_allowance_per_shift"] == 80.00
        assert data["monthly_salary"] == 15000.00

    def test_create_taproom_temp_worker(self, client, sample_temp_worker):
        """Test creating temporary worker (daily pay, no monthly)."""
        response = client.post("/api/v1/payroll/employees", json=sample_temp_worker)
        assert response.status_code == 201
        data = response.json()
        assert data["employment_type"] == "TEMPORARY"
        assert data["monthly_salary"] is None
        assert data["eligible_for_tips"] is True

    def test_list_employees(self, client, sample_brewery_employee):
        """Test listing employees."""
        client.post("/api/v1/payroll/employees", json=sample_brewery_employee)
        response = client.get("/api/v1/payroll/employees")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_get_employee(self, client, sample_brewery_employee):
        """Test getting single employee."""
        create = client.post("/api/v1/payroll/employees", json=sample_brewery_employee)
        eid = create.json()["id"]
        response = client.get(f"/api/v1/payroll/employees/{eid}")
        assert response.status_code == 200
        assert response.json()["full_name"] == "Miguel Ángel Rodríguez"

    def test_update_employee_salary(self, client, sample_brewery_employee):
        """Test updating salary recalculates monthly."""
        create = client.post("/api/v1/payroll/employees", json=sample_brewery_employee)
        eid = create.json()["id"]
        response = client.patch(
            f"/api/v1/payroll/employees/{eid}",
            json={"daily_salary": 1000.00},
        )
        assert response.status_code == 200
        assert response.json()["daily_salary"] == 1000.00
        assert response.json()["monthly_salary"] == 30000.00

    def test_filter_by_department(self, client, sample_brewery_employee, sample_taproom_employee):
        """Test filtering by department."""
        client.post("/api/v1/payroll/employees", json=sample_brewery_employee)
        client.post("/api/v1/payroll/employees", json=sample_taproom_employee)
        response = client.get("/api/v1/payroll/employees?department=TAPROOM")
        assert response.status_code == 200
        assert all(e["department"] == "TAPROOM" for e in response.json())

    def test_filter_by_employment_type(self, client, sample_taproom_employee, sample_temp_worker):
        """Test filtering by employment type."""
        client.post("/api/v1/payroll/employees", json=sample_taproom_employee)
        client.post("/api/v1/payroll/employees", json=sample_temp_worker)
        response = client.get("/api/v1/payroll/employees?employment_type=TEMPORARY")
        assert response.status_code == 200
        assert all(e["employment_type"] == "TEMPORARY" for e in response.json())

    def test_employee_not_found(self, client):
        """Test 404 for missing employee."""
        response = client.get("/api/v1/payroll/employees/99999")
        assert response.status_code == 404


class TestPayrollAPI:
    """Test payroll entry endpoints."""

    def test_create_payroll_entry(self, client, sample_brewery_employee):
        """Test creating a payroll entry with auto-calculation."""
        emp = client.post("/api/v1/payroll/employees", json=sample_brewery_employee).json()
        response = client.post("/api/v1/payroll/entries", json={
            "employee_id": emp["id"],
            "period_start": "2026-02-01T00:00:00",
            "period_end": "2026-02-07T00:00:00",
            "period_type": "WEEKLY",
            "days_worked": 6,
            "overtime_hours": 4,
            "overtime_rate": 150.00,
            "bonuses": 500.00,
            "deductions": 200.00,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["base_salary"] == 4999.98   # 833.33 × 6
        assert data["overtime_amount"] == 600.00  # 4 × 150
        assert data["total_payment"] == 5899.98   # 4999.98 + 600 + 500 - 200

    def test_payroll_with_tips_and_taxi(self, client, sample_taproom_employee):
        """Test payroll for taproom staff with tips and taxi."""
        emp = client.post("/api/v1/payroll/employees", json=sample_taproom_employee).json()
        response = client.post("/api/v1/payroll/entries", json={
            "employee_id": emp["id"],
            "period_start": "2026-02-16T00:00:00",
            "period_end": "2026-02-22T00:00:00",
            "period_type": "WEEKLY",
            "days_worked": 5,
            "tips_share": 1125.00,
            "taxi_shifts": 5,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["base_salary"] == 2500.00   # 500 × 5
        assert data["taxi_total"] == 400.00     # 5 × 80
        assert data["tips_share"] == 1125.00
        assert data["total_payment"] == 4025.00  # 2500 + 0 + 1125 + 400 - 0

    def test_temp_worker_daily_payroll(self, client, sample_temp_worker):
        """Test daily payroll for temp worker."""
        emp = client.post("/api/v1/payroll/employees", json=sample_temp_worker).json()
        response = client.post("/api/v1/payroll/entries", json={
            "employee_id": emp["id"],
            "period_start": "2026-02-20T00:00:00",
            "period_end": "2026-02-20T00:00:00",
            "period_type": "DAILY",
            "days_worked": 1,
            "tips_share": 500.00,
            "taxi_shifts": 1,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["base_salary"] == 350.00    # 350 × 1
        assert data["taxi_total"] == 80.00      # 1 × 80
        assert data["total_payment"] == 930.00   # 350 + 500 + 80

    def test_list_payroll(self, client, sample_brewery_employee):
        """Test listing payroll entries."""
        emp = client.post("/api/v1/payroll/employees", json=sample_brewery_employee).json()
        client.post("/api/v1/payroll/entries", json={
            "employee_id": emp["id"],
            "period_start": "2026-02-01T00:00:00",
            "period_end": "2026-02-07T00:00:00",
            "days_worked": 6,
        })
        response = client.get("/api/v1/payroll/entries")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_get_payroll_entry(self, client, sample_brewery_employee):
        """Test getting single payroll entry."""
        emp = client.post("/api/v1/payroll/employees", json=sample_brewery_employee).json()
        entry = client.post("/api/v1/payroll/entries", json={
            "employee_id": emp["id"],
            "period_start": "2026-02-01T00:00:00",
            "period_end": "2026-02-07T00:00:00",
            "days_worked": 6,
        }).json()
        response = client.get(f"/api/v1/payroll/entries/{entry['id']}")
        assert response.status_code == 200

    def test_mark_as_paid(self, client, sample_brewery_employee):
        """Test marking payroll entry as paid."""
        emp = client.post("/api/v1/payroll/employees", json=sample_brewery_employee).json()
        entry = client.post("/api/v1/payroll/entries", json={
            "employee_id": emp["id"],
            "period_start": "2026-02-01T00:00:00",
            "period_end": "2026-02-07T00:00:00",
            "days_worked": 6,
        }).json()
        response = client.patch(f"/api/v1/payroll/entries/{entry['id']}/pay")
        assert response.status_code == 200
        assert response.json()["payment_status"] == "PAID"

    def test_cannot_pay_twice(self, client, sample_brewery_employee):
        """Test double-pay prevention."""
        emp = client.post("/api/v1/payroll/employees", json=sample_brewery_employee).json()
        entry = client.post("/api/v1/payroll/entries", json={
            "employee_id": emp["id"],
            "period_start": "2026-02-01T00:00:00",
            "period_end": "2026-02-07T00:00:00",
            "days_worked": 6,
        }).json()
        client.patch(f"/api/v1/payroll/entries/{entry['id']}/pay")
        response = client.patch(f"/api/v1/payroll/entries/{entry['id']}/pay")
        assert response.status_code == 400


class TestTipPoolAPI:
    """Test weekly tip pool distribution."""

    def _create_taproom_staff(self, client, count=3):
        """Helper to create taproom employees eligible for tips."""
        employees = []
        for i in range(count):
            emp = client.post("/api/v1/payroll/employees", json={
                "full_name": f"Taproom Staff {i+1}",
                "role": "BARTENDER",
                "department": "TAPROOM",
                "employment_type": "FIXED",
                "daily_salary": 500.00,
                "eligible_for_tips": True,
            }).json()
            employees.append(emp)
        return employees

    def test_create_tip_pool(self, client):
        """Test creating weekly tip pool."""
        staff = self._create_taproom_staff(client, 3)
        ids = [s["id"] for s in staff]
        response = client.post("/api/v1/payroll/tip-pools", json={
            "week_start": "2026-02-15",
            "week_end": "2026-02-21",
            "total_collected": 4500.00,
            "participant_ids": ids,
            "notes": "Good week, Valentine's event",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["total_collected"] == 4500.00
        assert data["num_participants"] == 3
        assert data["per_person_share"] == 1500.00
        assert len(data["participants"]) == 3

    def test_tip_pool_with_temps(self, client):
        """Test tip pool including temp workers."""
        fixed = self._create_taproom_staff(client, 2)
        temp = client.post("/api/v1/payroll/employees", json={
            "full_name": "Temp Worker",
            "role": "WAITER",
            "department": "TAPROOM",
            "employment_type": "TEMPORARY",
            "daily_salary": 350,
            "eligible_for_tips": True,
        }).json()
        ids = [fixed[0]["id"], fixed[1]["id"], temp["id"]]
        response = client.post("/api/v1/payroll/tip-pools", json={
            "week_start": "2026-02-15",
            "week_end": "2026-02-21",
            "total_collected": 3000.00,
            "participant_ids": ids,
        })
        assert response.status_code == 201
        assert response.json()["per_person_share"] == 1000.00  # 3000 / 3

    def test_tip_pool_rejects_non_eligible(self, client, sample_brewery_employee):
        """Test that non-tip-eligible employees are rejected."""
        emp = client.post("/api/v1/payroll/employees", json=sample_brewery_employee).json()
        response = client.post("/api/v1/payroll/tip-pools", json={
            "week_start": "2026-02-15",
            "week_end": "2026-02-21",
            "total_collected": 3000.00,
            "participant_ids": [emp["id"]],
        })
        assert response.status_code == 400

    def test_list_tip_pools(self, client):
        """Test listing tip pools."""
        staff = self._create_taproom_staff(client, 2)
        ids = [s["id"] for s in staff]
        client.post("/api/v1/payroll/tip-pools", json={
            "week_start": "2026-02-15",
            "week_end": "2026-02-21",
            "total_collected": 3000.00,
            "participant_ids": ids,
        })
        response = client.get("/api/v1/payroll/tip-pools")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_get_tip_pool(self, client):
        """Test getting single tip pool."""
        staff = self._create_taproom_staff(client, 2)
        ids = [s["id"] for s in staff]
        pool = client.post("/api/v1/payroll/tip-pools", json={
            "week_start": "2026-02-15",
            "week_end": "2026-02-21",
            "total_collected": 2000.00,
            "participant_ids": ids,
        }).json()
        response = client.get(f"/api/v1/payroll/tip-pools/{pool['id']}")
        assert response.status_code == 200
        assert response.json()["total_collected"] == 2000.00
