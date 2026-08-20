#!/usr/bin/env bash
# Collect the built bundles into release/, dropping the -SNAPSHOT from the file name.
#
# The jars Tycho produces are named after the Maven version (13.0.0-SNAPSHOT), but the
# version OSGi actually sees is the Bundle-Version inside the jar, where .qualifier has
# been expanded to a build timestamp - so every build is distinguishable to Felix even
# though the file name is not. This script only renames; nothing about the bundle changes.
set -euo pipefail
cd "$(dirname "$0")"

rm -rf release && mkdir -p release
found=0
for jar in */target/*.jar; do
    case "$jar" in *-sources.jar) continue ;; esac
    [ -e "$jar" ] || continue
    name="$(basename "$jar")"
    cp "$jar" "release/${name/-SNAPSHOT/}"
    found=$((found + 1))
done

if [ "$found" -eq 0 ]; then
    echo "No jars found - build the modules first." >&2
    exit 1
fi

echo "release/ now holds:"
for f in release/*.jar; do
    printf '  %-52s Bundle-Version: %s\n' "$(basename "$f")" \
        "$(unzip -p "$f" META-INF/MANIFEST.MF | tr -d '\r' | sed -n 's/^Bundle-Version: //p')"
done
