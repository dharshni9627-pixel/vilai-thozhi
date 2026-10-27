import base64
import io
import json
import os
import sys
import tempfile
import unittest

# Use a throw-away database and force offline mode BEFORE importing the app
os.environ["SHG_DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["ANTHROPIC_API_KEY"] = ""
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as shg  # noqa: E402

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)
DEMO = {
    "name": "மாங்காய் ஊறுகாய்", "category": "pickle", "units": 10, "margin": 30,
    "packaging": 40, "labour": 150, "other": 30, "notes": "வீட்டிலேயே அரைத்த மசாலா",
    "ingredients": [{"name": "மாங்காய்", "cost": 120}, {"name": "நல்லெண்ணெய்", "cost": 60},
                    {"name": "மசாலா", "cost": 45}, {"name": "உப்பு", "cost": 10}],
}


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.c = shg.app.test_client()

    def gen(self, payload, photo=None):
        data = {"data": json.dumps(payload)}
        if photo:
            data["photo"] = photo
        return self.c.post("/api/generate", data=data, content_type="multipart/form-data")

    def test_tc30_pages_load(self):
        for path in ("/", "/calculator", "/products"):
            self.assertEqual(self.c.get(path).status_code, 200, path)

    def test_tc31_generate_offline(self):
        r = self.gen(DEMO)
        j = r.get_json()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(j["ai_mode"], "offline")
        self.assertEqual(j["cost"]["price"]["suggested"], 60)
        self.assertEqual(j["listing"]["title_ta"], DEMO["name"])
        self.assertIn("explanation_en", j["listing"])

    def test_tc32_generate_requires_name(self):
        self.assertEqual(self.gen({**DEMO, "name": " "}).status_code, 400)

    def test_tc33_generate_rejects_bad_costs(self):
        self.assertEqual(self.gen({"units": 5}).status_code, 400)
        self.assertEqual(self.gen({**DEMO, "packaging": -1}).status_code, 400)

    def test_tc34_photo_upload_and_cleanup(self):
        r = self.gen(DEMO, photo=(io.BytesIO(PNG), "p.png", "image/png"))
        j = r.get_json()
        self.assertEqual(r.status_code, 200)
        self.assertTrue(j["image_url"].startswith("/static/uploads/"))
        path = os.path.join(shg.UPLOAD_DIR, os.path.basename(j["image_url"]))
        self.assertTrue(os.path.isfile(path))
        os.remove(path)

    def test_tc35_photo_wrong_type_rejected(self):
        r = self.gen(DEMO, photo=(io.BytesIO(b"hello"), "x.txt", "text/plain"))
        self.assertEqual(r.status_code, 400)

    def test_tc36_save_list_delete(self):
        j = self.gen(DEMO).get_json()
        body = {"name": DEMO["name"], "category": "pickle", "cost": j["cost"], "listing": j["listing"], "image_url": None}
        s = self.c.post("/api/save", json=body)
        self.assertEqual(s.status_code, 200)
        pid = s.get_json()["id"]
        items = self.c.get("/api/products").get_json()
        self.assertIn(pid, [i["id"] for i in items])
        self.assertEqual(self.c.delete(f"/api/products/{pid}").status_code, 200)
        items = self.c.get("/api/products").get_json()
        self.assertNotIn(pid, [i["id"] for i in items])

    def test_tc37_save_incomplete_rejected(self):
        self.assertEqual(self.c.post("/api/save", json={"name": "x"}).status_code, 400)

    def test_tc38_save_ignores_external_image_url(self):
        j = self.gen(DEMO).get_json()
        body = {"name": "t", "category": "other", "cost": j["cost"], "listing": j["listing"],
                "image_url": "https://evil.example/x.png"}
        pid = self.c.post("/api/save", json=body).get_json()["id"]
        item = [i for i in self.c.get("/api/products").get_json() if i["id"] == pid][0]
        self.assertIsNone(item["image_url"])
        self.c.delete(f"/api/products/{pid}")

    def test_tc39_translate_offline_and_empty(self):
        r = self.c.post("/api/translate", json={"title": "மாங்காய் ஊறுகாய்", "description": "ஊறுகாய்"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["mode"], "offline")
        self.assertIn("mango", r.get_json()["title"])
        self.assertEqual(self.c.post("/api/translate", json={}).status_code, 400)


if __name__ == "__main__":
    unittest.main()
