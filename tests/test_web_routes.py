from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from app import create_app

from tests.fakes import FakeDatabase


class WebRoutesTests(unittest.TestCase):
    def setUp(self):
        os.environ["SECRET_KEY"] = "test-secret"
        os.environ["MONGO_URI"] = "mongodb://localhost:27017"
        os.environ["MONGO_DB_NAME"] = "RecipeLab_test"
        os.environ["LLM_PROVIDER"] = "openai_compatible"
        os.environ["LLM_MODEL"] = "gpt-5.4"

        self.app = create_app()
        self.client = self.app.test_client()
        self.fake_db = FakeDatabase()

    def tearDown(self):
        self.app.extensions["mongo_client"].close()

    @patch("app.blueprints.web.routes.get_mongo_db")
    def test_dashboard_renders(self, mock_db):
        mock_db.return_value = self.fake_db
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Recipe Dashboard", response.data)

    @patch("app.blueprints.web.routes.get_mongo_db")
    def test_generate_page_renders(self, mock_db):
        mock_db.return_value = self.fake_db
        response = self.client.get("/generate")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Generate a Recipe", response.data)

    @patch("app.blueprints.web.routes.get_mongo_db")
    @patch("app.blueprints.web.routes.generate_recipe_suggestion")
    def test_generate_post_redirects_to_suggestion_detail(self, mock_generate, mock_db):
        mock_db.return_value = self.fake_db
        mock_generate.return_value = {
            "ok": True,
            "status": "draft",
            "suggestion_id": "s1",
        }

        response = self.client.post(
            "/generate",
            data={
                "meal_type": "main",
                "instructions": "quick dinner",
                "model": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/suggestions/s1", response.location)

    @patch("app.blueprints.web.routes.get_mongo_db")
    @patch("app.blueprints.web.routes.generate_recipe_suggestion")
    def test_generate_post_handles_backend_error(self, mock_generate, mock_db):
        mock_db.return_value = self.fake_db
        mock_generate.side_effect = RuntimeError("db unavailable")

        response = self.client.post(
            "/generate",
            data={
                "meal_type": "main",
                "instructions": "quick dinner",
                "model": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/generate", response.location)

    @patch("app.blueprints.web.routes.get_mongo_db")
    def test_suggestions_page_renders(self, mock_db):
        mock_db.return_value = self.fake_db
        self.fake_db["suggestions"].docs.append(
            {
                "_id": "s1",
                "title": "Test Suggestion",
                "meal_type": "main",
                "status": "draft",
                "recipe": {"ingredients": [], "method": [], "metadata": {}},
                "validation": {"valid": True, "errors": []},
                "created_at": 1,
            }
        )

        response = self.client.get("/suggestions")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test Suggestion", response.data)

    @patch("app.blueprints.web.routes.get_mongo_db")
    def test_accept_suggestion_saves_recipe(self, mock_db):
        mock_db.return_value = self.fake_db
        self.fake_db["suggestions"].docs.append(
            {
                "_id": "s1",
                "title": "Test Suggestion",
                "meal_type": "main",
                "status": "draft",
                "recipe": {
                    "title": "Test Suggestion",
                    "meal_type": "main",
                    "source_type": "ai",
                    "metadata": {
                        "source": "AI Generated",
                        "servings": "2",
                        "prep_time": "10",
                        "cook_time": "20",
                        "rating": "",
                        "difficulty": "",
                        "tags": ["quick"],
                    },
                    "ingredients": [{"quantity": "1", "unit": "cup", "ingredient": "rice"}],
                    "method": ["Cook rice"],
                    "notes": [],
                },
                "validation": {"valid": True, "errors": []},
                "created_at": 1,
            }
        )

        response = self.client.post("/suggestions/s1/accept")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/recipes/", response.location)

        self.assertEqual(len(self.fake_db["recipes"].docs), 1)
        self.assertEqual(self.fake_db["suggestions"].docs[0]["status"], "accepted")


if __name__ == "__main__":
    unittest.main()
