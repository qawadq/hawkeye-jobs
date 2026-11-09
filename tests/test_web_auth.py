import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _bootstrap  # noqa: F401

from fastapi.testclient import TestClient
from web.server import create_app


class FakeStore:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def job_counts(self):
        return {"new": 0, "saved": 0, "applied": 0, "dismissed": 0}


class FakeManager:
    current = None


class FakeServices:
    manager = FakeManager()
    hosted = True
    store = False
    version = "1.0.0"

    def load_app_settings(self):
        return {"onboarding_done": True, "language": "ar", "theme": "auto",
                "latest_version": None, "update_check": False}

    def store_factory(self):
        return FakeStore()

    def find_chrome(self):
        return None

    def load_config(self):
        return None

    def background(self):
        return {"tray": False, "autostart": False}


class HostedAuthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.static = Path(self.temp.name)
        (self.static / "login.html").write_text("<h1>Private login</h1>", encoding="utf-8")
        self.app = create_app(
            token=None,
            allowed_hosts={"jobs.example.test"},
            services=FakeServices(),
            static_dir=self.static,
            web_password="a-long-personal-password",
            session_secret="s" * 48,
            cookie_secure=False,
        )
        self.client = TestClient(self.app, base_url="http://jobs.example.test")

    def tearDown(self):
        self.temp.cleanup()

    def test_unauthenticated_user_only_sees_login_and_health(self):
        self.assertIn("Private login", self.client.get("/").text)
        self.assertEqual(self.client.get("/api/state").status_code, 401)
        self.assertEqual(self.client.get("/api/auth/status").json(),
                         {"required": True, "authenticated": False})
        self.assertEqual(self.client.get("/healthz").json(), {"ok": True})

    def test_login_cookie_grants_access_and_logout_revokes_it(self):
        bad = self.client.post("/api/auth/login", json={"password": "wrong-password"})
        self.assertEqual(bad.status_code, 401)
        good = self.client.post("/api/auth/login", json={"password": "a-long-personal-password"})
        self.assertEqual(good.status_code, 200)
        self.assertTrue(self.client.get("/api/auth/status").json()["authenticated"])
        self.assertEqual(self.client.get("/api/state").status_code, 200)
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 204)
        self.assertEqual(self.client.get("/api/state").status_code, 401)

    def test_login_rate_limit(self):
        for _ in range(5):
            self.assertEqual(self.client.post("/api/auth/login", json={"password": "wrong-password"}).status_code, 401)
        response = self.client.post("/api/auth/login", json={"password": "wrong-password"})
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response.headers)

    def test_auth_configuration_must_be_strong_and_complete(self):
        with self.assertRaises(ValueError):
            create_app(token=None, allowed_hosts={"jobs.example.test"}, services=FakeServices(),
                       web_password="a-long-personal-password", session_secret=None)
        with self.assertRaises(ValueError):
            create_app(token=None, allowed_hosts={"jobs.example.test"}, services=FakeServices(),
                       web_password="short", session_secret="s" * 48)



class LocalModeHostRegressionTests(unittest.TestCase):
    def test_local_token_and_exact_host_port_guard_remain_compatible(self):
        temp = tempfile.TemporaryDirectory()
        try:
            static = Path(temp.name)
            (static / "index.html").write_text("<h1>Local desktop shell</h1>", encoding="utf-8")
            app = create_app(token="local-token", allowed_hosts={"127.0.0.1:8765"},
                             services=FakeServices(), static_dir=static)
            client = TestClient(app, base_url="http://127.0.0.1:8765")
            allowed = client.get("/api/state", headers={"X-Hawkeye-Token": "local-token"})
            denied = client.get("/api/state")
            self.assertEqual(allowed.status_code, 200)
            self.assertEqual(denied.status_code, 403)
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
