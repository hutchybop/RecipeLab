from __future__ import annotations

import unittest

from app.services.prompt_composer import compose_recipe_prompt


class PromptComposerTests(unittest.TestCase):
    def test_compose_prompt_contains_required_context(self):
        prompt = compose_recipe_prompt(
            meal_type="lunch_batch",
            instructions="high protein and meal-prep friendly",
            profile={
                "likes": ["lentils", "coriander"],
                "dislikes": ["heavy dairy"],
                "hard_avoids": ["peanuts", "sprouts"],
                "notes": "Prefer one-pot meals",
            },
        )

        self.assertIn("Meal type: lunch_batch", prompt)
        self.assertIn("high protein and meal-prep friendly", prompt)
        self.assertIn("lentils, coriander", prompt)
        self.assertIn("peanuts, sprouts", prompt)
        self.assertIn("Output JSON object schema", prompt)


if __name__ == "__main__":
    unittest.main()
