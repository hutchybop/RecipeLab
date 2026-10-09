from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from app import create_app
from app.services.generation_service import generate_recipe_suggestion

from tests.fakes import FakeDatabase


class RuntimeSettingsTests(unittest.TestCase):
    def setUp(self):
        os.environ["SECRET_KEY"] = "test-secret"
        os.environ["MONGO_URI"] = "mongodb://localhost:27017"
        os.environ["MONGO_DB_NAME"] = "recipelab_test"
        os.environ["LLM_PROVIDER"] = "openai_compatible"
        os.environ["LLM_MODEL"] = "gpt-5.4"
        os.environ["LLM_ALLOWED_MODELS"] = "gpt-5.4,deepseek-v4.1-flash"

        self.app = create_app()
        self.db = FakeDatabase()

    def tearDown(self):
        self.app.extensions["mongo_client"].close()

    @patch("app.services.generation_service.LLMAdapter.generate_recipe")
    def test_generate_uses_runtime_selected_model(self, mock_generate):
        mock_generate.return_value = json.dumps(
            {
                "title": "Runtime Model Recipe",
                "source": "AI Generated",
                "ingredients": [{"quantity": "1", "unit": "cup", "ingredient": "rice"}],
                "method": ["Cook"],
                "notes": [],
            }
        )
        self.db["runtime_settings"].docs.append(
            {
                "_id": "rs1",
                "key": "generation_model",
                "value": "deepseek-v4.1-flash",
            }
        )

        with self.app.app_context():
            result = generate_recipe_suggestion(
                db=self.db,
                meal_type="main",
                instructions="quick",
            )

        self.assertTrue(result["ok"])
        self.assertEqual(
            self.db["generation_runs"].docs[0]["model"], "deepseek-v4.1-flash"
        )


if __name__ == "__main__":
    unittest.main()
