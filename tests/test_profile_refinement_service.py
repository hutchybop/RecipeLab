from __future__ import annotations

import unittest

from app.services.profile_refinement_service import (
    apply_profile_update_suggestion,
    generate_profile_update_suggestions,
    reject_profile_update_suggestion,
    _extract_tokens,
)

from tests.fakes import FakeDatabase


class ProfileRefinementServiceTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeDatabase()
        self.db["preferences"].docs.append(
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

    def test_generate_profile_update_suggestions_creates_pending_items(self):
        self.db["recipes"].docs.append(
            {
                "_id": "r1",
                "title": "Chicken Bowl",
                "metadata": {"tags": ["spicy"]},
                "ingredients": [
                    {"quantity": "1", "unit": "lb", "ingredient": "chicken breast"},
                    {"quantity": "1", "unit": "cup", "ingredient": "rice"},
                ],
            }
        )
        self.db["recipes"].docs.append(
            {
                "_id": "r2",
                "title": "Chicken and Rice",
                "metadata": {"tags": ["spicy"]},
                "ingredients": [
                    {"quantity": "1", "unit": "lb", "ingredient": "chicken breast"},
                    {"quantity": "1", "unit": "cup", "ingredient": "rice"},
                ],
            }
        )
        self.db["feedback_events"].docs.extend(
            [
                {
                    "_id": "f1",
                    "target_type": "recipe",
                    "target_id": "r1",
                    "signal": "liked",
                    "created_at": 2,
                },
                {
                    "_id": "f2",
                    "target_type": "recipe",
                    "target_id": "r1",
                    "signal": "liked",
                    "created_at": 1,
                },
                {
                    "_id": "f3",
                    "target_type": "recipe",
                    "target_id": "r2",
                    "signal": "liked",
                    "created_at": 0,
                },
            ]
        )

        result = generate_profile_update_suggestions(self.db, min_support=2)
        self.assertGreaterEqual(result["created"], 1)
        self.assertGreaterEqual(len(self.db["profile_update_suggestions"].docs), 1)

    def test_apply_and_reject_profile_update_suggestions(self):
        self.db["profile_update_suggestions"].docs.append(
            {
                "_id": "u1",
                "action": "add_like",
                "token": "chicken",
                "support_count": 3,
                "status": "pending",
                "notes": "",
            }
        )

        ok, _ = apply_profile_update_suggestion(self.db, "u1")
        self.assertTrue(ok)
        self.assertIn(
            "chicken",
            [item.lower() for item in self.db["preferences"].docs[0]["likes"]],
        )
        self.assertEqual(
            self.db["profile_update_suggestions"].docs[0]["status"], "applied"
        )

        self.db["profile_update_suggestions"].docs.append(
            {
                "_id": "u2",
                "action": "add_dislike",
                "token": "mushroom",
                "support_count": 2,
                "status": "pending",
                "notes": "",
            }
        )
        rejected = reject_profile_update_suggestion(self.db, "u2")
        self.assertTrue(rejected)
        self.assertEqual(
            self.db["profile_update_suggestions"].docs[1]["status"], "rejected"
        )

    def test_generate_profile_update_suggestions_uses_latest_reaction_per_target(self):
        self.db["recipes"].docs.append(
            {
                "_id": "r1",
                "title": "Chicken Bowl",
                "metadata": {"tags": ["spicy"]},
                "ingredients": [
                    {"quantity": "1", "unit": "lb", "ingredient": "chicken breast"},
                ],
            }
        )
        self.db["feedback_events"].docs.extend(
            [
                {
                    "_id": "f2",
                    "target_type": "recipe",
                    "target_id": "r1",
                    "signal": "liked",
                    "created_at": 2,
                },
                {
                    "_id": "f1",
                    "target_type": "recipe",
                    "target_id": "r1",
                    "signal": "disliked",
                    "created_at": 1,
                },
            ]
        )

        result = generate_profile_update_suggestions(self.db, min_support=1)
        self.assertGreaterEqual(result["created"], 1)
        actions = {
            (item["action"], item["token"])
            for item in self.db["profile_update_suggestions"].docs
        }
        self.assertIn(("add_like", "chicken breast"), actions)
        self.assertNotIn(("add_dislike", "chicken breast"), actions)

    def test_extract_tokens_preserves_ingredient_phrases_and_removes_prep_noise(self):
        tokens = _extract_tokens(
            {
                "metadata": {"tags": ["brown-rice"]},
                "ingredients": [
                    {"ingredient": "brown rice"},
                    {"ingredient": "dark chocolate, melted"},
                    {"ingredient": "thin steaks, chopped"},
                    {"ingredient": "red onion, skin removed"},
                ],
            }
        )

        self.assertEqual(
            tokens,
            {"brown rice", "dark chocolate", "steaks", "red onion"},
        )

    def test_refresh_rejects_obsolete_single_word_suggestions(self):
        for recipe_id in ("r1", "r2"):
            self.db["recipes"].docs.append(
                {
                    "_id": recipe_id,
                    "title": "Brown Rice Bowl",
                    "metadata": {"tags": []},
                    "ingredients": [{"ingredient": "brown rice"}],
                }
            )
            self.db["feedback_events"].docs.append(
                {
                    "_id": f"f-{recipe_id}",
                    "target_type": "recipe",
                    "target_id": recipe_id,
                    "signal": "liked",
                    "created_at": 1,
                }
            )

        self.db["profile_update_suggestions"].docs.extend(
            [
                {
                    "_id": "old-brown",
                    "action": "add_like",
                    "token": "brown",
                    "support_count": 2,
                    "status": "pending",
                    "created_at": 1,
                },
                {
                    "_id": "old-rice",
                    "action": "add_like",
                    "token": "rice",
                    "support_count": 2,
                    "status": "pending",
                    "created_at": 2,
                },
            ]
        )

        generate_profile_update_suggestions(self.db, min_support=2)

        suggestions = self.db["profile_update_suggestions"].docs
        pending = {
            item["token"] for item in suggestions if item.get("status") == "pending"
        }
        self.assertEqual(pending, {"brown rice"})
        self.assertTrue(
            all(
                item.get("status") == "rejected"
                for item in suggestions
                if item["token"] in {"brown", "rice"}
            )
        )


if __name__ == "__main__":
    unittest.main()
