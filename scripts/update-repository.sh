#!/usr/bin/env bash
# Builds the site in _site/: copies the static files and debs/, indexes debs/ with
# apt-ftparchive into Packages, Packages.gz, Packages.xz and Release (a flat repository:
# the indexes sit at the site root and every Filename is debs/<file>.deb).
# Run by .github/workflows/update-repository.yml on every push to main; it can be run by
# hand too. It never changes a .deb and writes nothing outside the output folder.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE_URL="${SITE_URL:-https://imod-commission.github.io/imod-repo}"
SITE_URL="${SITE_URL%/}"
OUT="${OUT_DIR:-$ROOT/_site}"

cd "$ROOT"
ls debs/*.deb >/dev/null 2>&1 || { echo "error: no .deb in debs/" >&2; exit 1; }

# The same Package, Version and Architecture twice would confuse clients.
dups="$(for f in debs/*.deb; do dpkg-deb -f "$f" Package Version Architecture | paste -sd' ' -; done | sort | uniq -d)"
if [ -n "$dups" ]; then
  echo "error: duplicate package/version/architecture:" >&2
  echo "$dups" >&2
  exit 1
fi

: "${OUT:?}"
rm -rf "$OUT"
mkdir -p "$OUT"
cp -R debs "$OUT/debs"
if [ -d depictions ]; then cp -R depictions "$OUT/depictions"; fi
for f in index.html CydiaIcon.png sileo-featured.json; do
  if [ -f "$f" ]; then cp "$f" "$OUT/$f"; fi
done
touch "$OUT/.nojekyll"

cd "$OUT"
# 1. Index. The relative path "debs" gives Filename: debs/<file>.deb.
apt-ftparchive packages debs > Packages.raw
# 2. Add Depiction/SileoDepiction/Icon and fill what old debs lack.
python3 "$ROOT/scripts/inject-metadata.py" "$SITE_URL" "$ROOT/depictions" < Packages.raw > Packages
rm -f Packages.raw
gzip -9 -n -c Packages > Packages.gz
xz -9 -c Packages > Packages.xz

# 3. Release: hash only the index files, not the debs.
idx="$(mktemp -d)"
cp Packages Packages.gz Packages.xz "$idx/"
apt-ftparchive \
  -o APT::FTPArchive::Release::Origin="imod" \
  -o APT::FTPArchive::Release::Label="imod" \
  -o APT::FTPArchive::Release::Suite="stable" \
  -o APT::FTPArchive::Release::Codename="ios" \
  -o APT::FTPArchive::Release::Architectures="iphoneos-arm iphoneos-arm64 iphoneos-arm64e" \
  -o APT::FTPArchive::Release::Components="main" \
  -o APT::FTPArchive::Release::Description="Tweaks by imod_commission" \
  release "$idx" > Release
rm -rf "$idx"

# 3b. Ratings: combine the frozen YouRepo votes (data/yourepo-baseline.json) with the votes cast
# as GitHub issues, and patch the COPIES of the depictions in the site (the committed files stay
# as they are). If the issues cannot be read, fetch-ratings.py falls back to the baseline and
# only warns. A failure here never stops the deploy: the unpatched depictions are still valid.
ratings_json="$(mktemp)"
if python3 "$ROOT/scripts/fetch-ratings.py" --out "$ratings_json" \
   && python3 "$ROOT/scripts/patch-depictions.py" "$OUT" "$ratings_json"; then
  :
else
  echo "warning: could not add ratings to the depictions; publishing them without" >&2
  if [ -n "${GITHUB_ACTIONS:-}" ]; then echo "::warning::could not add ratings to the depictions"; fi
fi
rm -f "$ratings_json"

# 4. Sanity checks: fail the build rather than publish a broken source.
test -s Packages && test -s Packages.xz && test -s Release
n_debs="$(ls debs/*.deb | wc -l | tr -d ' ')"
n_pkgs="$(grep -c '^Package: ' Packages || true)"
n_sec="$(grep -c '^Section: ' Packages || true)"
[ "$n_debs" = "$n_pkgs" ] || { echo "error: $n_debs debs but $n_pkgs entries in Packages" >&2; exit 1; }
[ "$n_sec" = "$n_pkgs" ] || { echo "error: a package has no Section" >&2; exit 1; }
if [ -f sileo-featured.json ]; then python3 -c 'import json,sys;json.load(open(sys.argv[1]))' sileo-featured.json; fi
for j in depictions/*/depiction.json; do
  if [ -f "$j" ]; then python3 -c 'import json,sys;json.load(open(sys.argv[1]))' "$j"; fi
done

echo "Built $OUT: $n_pkgs packages for $SITE_URL"
