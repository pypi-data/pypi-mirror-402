#!/bin/bash
#
# do the necessary things to build and publish python project
#

# Status tracking: 0=pending, 1=done, 2=failed
declare -a STATUS=(0 0 0 0 0 0)

# Action functions
action_1_convert_readme() {
    if [ -f README.org ]; then
        echo "i... converting org to md by force"
        if pandoc README.org -o README.md; then
            STATUS[0]=1
            echo "✓ README.org converted to README.md"
        else
            STATUS[0]=2
            echo "✗ Failed to convert README.org"
        fi
    else
        echo "✗ README.org not found, cannot convert"
        STATUS[0]=2
    fi
}

action_2_git_check() {
    git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]

    if [ "$?" != "0" ]; then
        echo "x... git is not clean... committing automatically"
        sleep 1
        if git commit -a -m "debug with automatic commit"; then
            STATUS[1]=1
            echo "✓ Git auto-commit successful"
        else
            STATUS[1]=2
            echo "✗ Git auto-commit failed"
        fi
    else
        echo "i... git is clean"
        STATUS[1]=1
    fi
}

action_3_clean_dist() {
    if [ -d "dist" ]; then
        echo "i... cleaning dist/"
        if rm -f dist/*; then
            STATUS[2]=1
            echo "✓ dist/ cleaned"
        else
            STATUS[2]=2
            echo "✗ Failed to clean dist/"
        fi
    else
        echo "✗ dist/ doesn't exist, cannot clean"
        STATUS[2]=2
    fi
}

action_4_bump_version() {
    if [ ! -f .bumpversion.cfg ]; then
        echo "i... creating .bumpversion.cfg (version 0.1.0)"
        cat <<EOF > .bumpversion.cfg
[bumpversion]
current_version = 0.1.0
commit = True
tag = True

[bumpversion:file:pyproject.toml]
search = version = "{current_version}"
replace = version = "{new_version}"
EOF
    fi

    echo "i... bumping version (patch)"
    if bumpversion patch; then
        echo "i... pushing to origin with tags"
        if git push origin --all && git push origin --tags; then
            STATUS[3]=1
            echo "✓ Version bumped and pushed"
        else
            STATUS[3]=2
            echo "✗ Failed to push to origin"
        fi
    else
        STATUS[3]=2
        echo "✗ Failed to bump version"
    fi
}

action_5_build() {
    echo "i... running uv build"
    if uv build; then
        STATUS[4]=1
        echo "✓ Build successful"
    else
        STATUS[4]=2
        echo "✗ Build failed"
    fi
}

action_6_publish() {
    echo "i... publishing to PyPI"
    tok=$(cat ~/.pypirc | grep pass | awk '{print$3}')
    if [ -z "$tok" ]; then
        STATUS[5]=2
        echo "✗ Failed to read token from ~/.pypirc"
        return
    fi

    if uv publish --username __token__ --password "$tok"; then
        STATUS[5]=1
        echo "✓ Published to PyPI"
    else
        STATUS[5]=2
        echo "✗ Failed to publish to PyPI"
    fi
}

# Display menu
show_menu() {
    clear
    echo "---------------------------------------------------------------"
    echo "____ speed up publishing to pypi ______________________________"
    echo "---------------------------------------------------------------"
    echo ""
    echo "Status | Key | Action"
    echo "-------|-----|---------------------------------------"

    local symbols=("[ ]" "[✓]" "[✗]")

    echo "  ${symbols[${STATUS[0]}]}  | 1   | Convert README.org to README.md"
    echo "  ${symbols[${STATUS[1]}]}  | 2   | Check git status / auto-commit"
    echo "  ${symbols[${STATUS[2]}]}  | 3   | Delete dist/* contents"
    echo "  ${symbols[${STATUS[3]}]}  | 4   | Bump version (patch) and push tags"
    echo "  ${symbols[${STATUS[4]}]}  | 5   | Run uv build"
    echo "  ${symbols[${STATUS[5]}]}  | 6   | Run uv publish with token"
    echo "       |-----|---------------------------------------"
    echo "       | a   | Run all actions in order"
    echo "       | r   | Reset all status"
    echo "       | q   | Quit"
    echo ""
    echo -n "Press a key to execute an action: "
}

# Run all actions in order
run_all() {
    action_1_convert_readme
    echo ""
    action_2_git_check
    echo ""
    action_3_clean_dist
    echo ""
    action_4_bump_version
    echo ""
    action_5_build
    echo ""
    action_6_publish
}

# Reset all status
reset_status() {
    STATUS=(0 0 0 0 0 0)
}

# Main loop
while true; do
    show_menu
    read -n 1 -r key
    echo ""
    echo ""

    case $key in
        1) action_1_convert_readme ;;
        2) action_2_git_check ;;
        3) action_3_clean_dist ;;
        4) action_4_bump_version ;;
        5) action_5_build ;;
        6) action_6_publish ;;
        a|A) run_all ;;
        r|R) reset_status; continue ;;
        q|Q) echo "Exiting..."; exit 0 ;;
        *) echo "Invalid option"; sleep 1; continue ;;
    esac

    sleep 1
done
