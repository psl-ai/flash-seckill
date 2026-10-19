from locust import HttpUser, between, task
import uuid


class RegistrationUser(HttpUser):
    wait_time = between(0.01, 0.05)
    activity_id = 1

    def on_start(self):
        self.email = f"load-{uuid.uuid4().hex[:10]}@example.com"
        response = self.client.post("/api/v1/auth/register", json={"email": self.email, "password": "Passw0rd!123", "display_name": "load"})
        if response.ok:
            self.token = response.json()["data"]["access_token"]
        else:
            login = self.client.post("/api/v1/auth/login", data={"username": self.email, "password": "Passw0rd!123"})
            self.token = login.json().get("data", {}).get("access_token", "")

    @task
    def register(self):
        self.client.post(
            f"/api/v1/activities/{self.activity_id}/registrations",
            headers={"Authorization": f"Bearer {self.token}", "Idempotency-Key": uuid.uuid4().hex},
            json={},
        )
