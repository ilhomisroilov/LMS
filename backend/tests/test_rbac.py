from tests.conftest import auth_header


def test_student_cannot_list_students(client):
    h = auth_header(client, "+998901000101", "student123")
    assert client.get("/api/v1/students", headers=h).status_code == 403


def test_admin_can_list_students(client):
    h = auth_header(client, "+998901112233", "Admin12345")
    r = client.get("/api/v1/students", headers=h)
    assert r.status_code == 200 and r.json()["total"] >= 1


def test_student_self_service(client):
    h = auth_header(client, "+998901000101", "student123")
    assert client.get("/api/v1/me/groups", headers=h).status_code == 200
    assert client.get("/api/v1/me/payments", headers=h).status_code == 200


def test_parent_self_service_is_limited_to_linked_children(client):
    h = auth_header(client, "+998901000010", "parent123")
    children = client.get("/api/v1/me/children", headers=h)
    assert children.status_code == 200
    assert [child["phone"] for child in children.json()] == ["+998901000101"]

    child_id = children.json()[0]["id"]
    for resource in ("attendance", "payments", "lessons"):
        response = client.get(
            f"/api/v1/me/children/{child_id}/{resource}", headers=h
        )
        assert response.status_code == 200, response.text

    admin = auth_header(client, "+998901112233", "Admin12345")
    students = client.get("/api/v1/students?size=100", headers=admin).json()["items"]
    unrelated_id = next(s["id"] for s in students if s["phone"] == "+998901000103")
    assert client.get(
        f"/api/v1/me/children/{unrelated_id}/attendance", headers=h
    ).status_code == 404
