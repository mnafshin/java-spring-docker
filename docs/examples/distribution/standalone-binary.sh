#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-0.1.0}"
ARCHIVE_URL="https://github.com/mnafshin/java-spring-docker/releases/download/v${VERSION}/springdocker-linux-amd64.tar.gz"

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

curl -fsSL "$ARCHIVE_URL" -o "$tmpdir/springdocker.tar.gz"
tar -xzf "$tmpdir/springdocker.tar.gz" -C "$tmpdir"
exec "$tmpdir/springdocker" "${@:2}"
