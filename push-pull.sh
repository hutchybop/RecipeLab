#!/bin/bash

#!/bin/bash

# # Run code formatting and linting
# echo "Running Black formatter..."
# black .
# echo "Running Flake8 linter..."
# flake8 .

# # Check if linting passed
# if [ $? -ne 0 ]; then
#     echo "❌ Flake8 found issues. Please fix them before committing."
#     exit 1
# fi
# echo "✅ All checks passed!"

# --- Update git ---
update_git() {
    # Stage all changes
    git add -A

    # Ask for commit message
    read -p "Enter commit message: " message

    # Commit with message
    git commit -m "$message"

    # # Stash any untracked changes (just in case)
    # git stash push -u -m "Auto-stash before pull"

    # # Pull latest from remote
    # git pull --rebase

    # # Reapply any stashed changes (if they exist)
    # git stash pop || echo "No stash to apply"

    # Push to current branch
    git push
}

update_git

# # --- Ask user if they want to run update_git ---
# echo
# read -p "Do you need to run /dev-log in opencode? (y/n): " answer

# case "$answer" in
#     n|N|no|NO)
#         update_git
#         ;;
#     y|Y|yes|YES)
#         echo "Closing..."
#         exit 0
#         ;;
#     *)
#         echo "Invalid option. Closing..."
#         exit 1
#         ;;
# esac