from __future__ import annotations

import unittest

from app.services.pdf_export_service import render_recipe_pdf


class PdfExportServiceTests(unittest.TestCase):
    def test_pdf_uses_safe_top_margin(self):
        pdf = render_recipe_pdf(
            {
                "title": "Margin Check",
                "meal_type": "main",
                "source_type": "user",
                "metadata": {},
                "ingredients": [{"quantity": "1", "unit": "cup", "ingredient": "rice"}],
                "method": ["Cook rice"],
                "notes": [],
            }
        )

        self.assertTrue(pdf.startswith(b"%PDF-1.4"))
        self.assertIn(b"50 742 Td", pdf)


if __name__ == "__main__":
    unittest.main()
