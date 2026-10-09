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
    def test_import_page_renders(self, mock_db):
        mock_db.return_value = self.fake_db
        response = self.client.get("/import")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Import Raw Recipe", response.data)

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
    @patch("app.blueprints.web.routes.convert_raw_recipe_to_suggestion")
    def test_import_post_redirects_to_suggestion_detail(self, mock_convert, mock_db):
        mock_db.return_value = self.fake_db
        mock_convert.return_value = {
            "ok": True,
            "status": "draft",
            "suggestion_id": "s2",
        }

        response = self.client.post(
            "/import",
            data={
                "meal_type": "main",
                "raw_recipe_text": "Title\nIngredients\nMethod",
                "model": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/suggestions/s2", response.location)

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
    def test_profile_page_renders(self, mock_db):
        mock_db.return_value = self.fake_db
        self.fake_db["preferences"].docs.append(
            {
                "_id": "p1",
                "profile_name": "default",
                "active": True,
                "hard_avoids": ["peanuts"],
                "likes": ["chicken"],
                "dislikes": [],
                "notes": "",
                "weights": {},
            }
        )

        response = self.client.get("/profile")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Tasting Profile", response.data)

    @patch("app.blueprints.web.routes.get_mongo_db")
    def test_feedback_post_creates_event(self, mock_db):
        mock_db.return_value = self.fake_db
        response = self.client.post(
            "/feedback",
            data={
                "target_type": "recipe",
                "target_id": "r1",
                "signal": "liked",
                "notes": "Great",
                "return_to": "/recipes",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(self.fake_db["feedback_events"].docs), 1)

    @patch("app.blueprints.web.routes.get_mongo_db")
    def test_apply_profile_suggestion_route(self, mock_db):
        mock_db.return_value = self.fake_db
        self.fake_db["preferences"].docs.append(
            {
                "_id": "p1",
                "profile_name": "default",
                "active": True,
                "hard_avoids": [],
                "likes": [],
                "dislikes": [],
                "notes": "",
                "weights": {},
            }
        )
        self.fake_db["profile_update_suggestions"].docs.append(
            {
                "_id": "u1",
                "action": "add_like",
                "token": "chicken",
                "support_count": 2,
                "status": "pending",
                "notes": "",
            }
        )

        response = self.client.post("/profile/suggestions/u1/apply")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/profile", response.location)

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

    @patch("app.blueprints.web.routes.get_mongo_db")
    def test_edit_suggestion_updates_and_sets_draft(self, mock_db):
        mock_db.return_value = self.fake_db
        self.fake_db["suggestions"].docs.append(
            {
                "_id": "s-edit",
                "title": "Draft Suggestion",
                "meal_type": "main",
                "status": "draft_invalid",
                "recipe": {
                    "title": "Draft Suggestion",
                    "meal_type": "main",
                    "source_type": "user",
                    "metadata": {"source": "", "servings": "", "prep_time": "", "cook_time": "", "rating": "", "difficulty": "", "tags": []},
                    "ingredients": [{"quantity": "1", "unit": "cup", "ingredient": "rice"}],
                    "method": ["Cook rice"],
                    "notes": [],
                },
                "validation": {"valid": False, "errors": ["bad format"]},
                "created_at": 1,
            }
        )

        response = self.client.post(
            "/suggestions/s-edit/edit",
            data={
                "title": "Edited Suggestion",
                "meal_type": "main",
                "source_type": "user",
                "source": "",
                "servings": "2",
                "prep_time": "5",
                "cook_time": "10",
                "difficulty": "",
                "rating": "",
                "tags": "quick",
                "ingredients": "1 cup rice",
                "method": "Cook rice",
                "notes": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/suggestions/s-edit", response.location)
        self.assertEqual(self.fake_db["suggestions"].docs[0]["status"], "draft")
        self.assertEqual(self.fake_db["suggestions"].docs[0]["title"], "Edited Suggestion")

    @patch("app.blueprints.web.routes.get_mongo_db")
    def test_edit_recipe_updates_title(self, mock_db):
        mock_db.return_value = self.fake_db
        self.fake_db["recipes"].docs.append(
            {
                "_id": "r1",
                "title": "Old Title",
                "meal_type": "main",
                "source_type": "user",
                "ingredients": [{"quantity": "1", "unit": "cup", "ingredient": "rice"}],
                "method": ["Cook rice"],
                "notes": [],
                "metadata": {
                    "source": "",
                    "servings": "1",
                    "prep_time": "5",
                    "cook_time": "10",
                    "rating": "",
                    "difficulty": "",
                    "tags": [],
                },
                "deleted_at": None,
            }
        )

        response = self.client.post(
            "/recipes/r1/edit",
            data={
                "title": "New Title",
                "meal_type": "main",
                "source_type": "user",
                "source": "",
                "servings": "1",
                "prep_time": "5",
                "cook_time": "10",
                "difficulty": "",
                "rating": "",
                "tags": "",
                "ingredients": "1 cup rice",
                "method": "Cook rice",
                "notes": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/recipes/r1", response.location)
        self.assertEqual(self.fake_db["recipes"].docs[0]["title"], "New Title")

    @patch("app.blueprints.web.routes.get_mongo_db")
    def test_delete_recipe_soft_deletes(self, mock_db):
        mock_db.return_value = self.fake_db
        self.fake_db["recipes"].docs.append(
            {
                "_id": "r2",
                "title": "Delete Me",
                "meal_type": "main",
                "source_type": "user",
                "ingredients": [{"quantity": "1", "unit": "cup", "ingredient": "rice"}],
                "method": ["Cook rice"],
                "notes": [],
                "metadata": {
                    "source": "",
                    "servings": "1",
                    "prep_time": "5",
                    "cook_time": "10",
                    "rating": "",
                    "difficulty": "",
                    "tags": [],
                },
                "deleted_at": None,
            }
        )

        response = self.client.post("/recipes/r2/delete")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/recipes", response.location)
        self.assertIsNotNone(self.fake_db["recipes"].docs[0]["deleted_at"])


if __name__ == "__main__":
    unittest.main()
