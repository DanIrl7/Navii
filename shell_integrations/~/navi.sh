navi() {
    local selected_dir=$(PYTHONPATH="." python -m src.navii.main)
    if [ -n "$selected_dir" ]; then
        cd "$selected_dir"
        fi
}