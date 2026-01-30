if (Test-Path dist) {
    rm -r dist
}

uv build
uv publish
