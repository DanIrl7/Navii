nyxx() {
    # Interactive CLI subcommands (nyxx jump add / nyxx memo add) need the
    # terminal for input() prompts, so run them directly without capturing.
    if [[ "$1" == "jump" && "$2" == "add" ]] || [[ "$1" == "memo" && "$2" == "add" ]]; then
        PYTHONPATH="." python -m src.nyxx.main "$@"
        return
    fi

    # TUI + lookup commands: capture only the final output line.
    # Curses draws to /dev/tty directly (see run_tui in main.py), so only the
    # single CD:/EXEC: line reaches this variable via $() capture.
    local output
    output=$(PYTHONPATH="." python -m src.nyxx.main "$@" 2>/dev/null)

    # Nothing printed — user quit without selecting anything
    if [ -z "$output" ]; then
        return 0
    fi

    # CD: prefix — change directory
    if [[ "$output" == CD:* ]]; then
        local target="${output#CD:}"
        cd "$target" || echo "nyxx: cd failed: $target"
        return
    fi

    # EXEC: prefix — run the saved command in the current shell so things
    # like `source venv/bin/activate` actually affect the caller.
    if [[ "$output" == EXEC:* ]]; then
        local cmd="${output#EXEC:}"
        eval "$cmd"
        return
    fi

    # Unexpected output — print it so nothing is silently lost
    echo "nyxx: unexpected output: $output"
}
