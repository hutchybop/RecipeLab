# AGENTS.md

This is a personal recipe collection — plain markdown files, no build system.

## Recipe Formatting

When creating or modifying recipes, use the canonical format defined in `prompts/canonical_recipe_formatter_prompt.md`:

```
---
title:
source:
servings:
prep_time:
cook_time:
rating:
difficulty:
tags: []
---

## Ingredients
- ...

## Method
1. ...

## Notes
(optional)
```

- Do NOT guess missing metadata — leave fields empty
- Normalise: quantity + unit + ingredient (lowercase)
- Use `Method` not "Preparation Steps"

## Tasting Profile Constraints

Before creating new recipes, check `tasting-profile.md` for:
- **Must avoid**: whole chickpeas, peanuts, sprouts, cauliflower, cinnamon
- **Preferred proteins**: legumes (lentils, beans), chicken, salmon
- **Preferred cuisines**: Indian, Asian, Mediterranean
- **Time constraint**: weekday meals under 45 minutes

## Directory Structure

- `main/` — main meal recipes
- `lunch/` — lunch recipes (often batch-cookable)
- `dessert/` — dessert recipes
- `AI-suggested/` — AI-generated recipe suggestions (not yet cooked)
- `prompts/` — LLM prompts for recipe generation

## No Development Commands

This repo has no code, tests, or CI. Work directly with markdown files.