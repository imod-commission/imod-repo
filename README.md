# imod package source

APT repository for iOS jailbreak package managers (Sileo, Zebra, Irisin, Cydia…), tweaks by
imod_commission. It is served by GitHub Pages:

**https://imod-commission.github.io/imod-repo/**

## Add the source

- Sileo: open [sileo://source/https://imod-commission.github.io/imod-repo/](sileo://source/https://imod-commission.github.io/imod-repo/)
  or add the URL above by hand in Sources.
- Other package managers: add `https://imod-commission.github.io/imod-repo/` as a source.

The packages here use the real IDs (`com.imodcommission.*`). If you installed them from the old
YouRepo source (`com.yourepo.imod.*`), remove the YouRepo packages first: the IDs changed, so they
are different packages and would otherwise conflict.

Architectures: `iphoneos-arm`, `iphoneos-arm64` (rootless) and `iphoneos-arm64e` (roothide). Your
package manager shows only the builds that fit your device.

## Layout

| Path | What it is |
| --- | --- |
| `debs/` | Every package, one `.deb` each, named `<Package>_<Version>_<Architecture>.deb`. Never edited or rebuilt here. |
| `depictions/<package id>/` | `depiction.json` (native Sileo depiction), `index.html` (web depiction), `icon.png`, `screenshots/` |
| `index.html`, `CydiaIcon.png` | The source's home page and icon |
| `scripts/update-repository.sh` | Builds the site: indexes `debs/` with `apt-ftparchive` into `Packages`, `Packages.gz`, `Packages.xz`, `Release` |
| `scripts/inject-metadata.py` | Adds `Depiction`, `SileoDepiction` and `Icon` to each package entry of the index (the old debs do not carry them) and fills a missing `Name`, `Maintainer`, `Author` or `Section` |
| `.github/workflows/update-repository.yml` | On every push to `main`, runs the script and publishes the result to GitHub Pages |
| `migration/` | Data archived from YouRepo (see below). Not published. |

`Packages`, `Packages.gz`, `Packages.xz`, `Release` and `_site/` are generated on GitHub, never
commit them.

## Add a new version

1. Put the new `.deb` in `debs/`, named `<Package>_<Version>_<Architecture>.deb`. **Add a file, never
   replace an existing one**: clients compare it with the index they cached. Old versions stay (the
   newest few are enough; remove older ones with `git rm`).
2. Update `depictions/<package id>/depiction.json` (version row, a new entry at the top of the
   Changelog tab) and `index.html` in the same folder.
3. Commit and push to `main`. The workflow rebuilds the index; the source updates within a few
   minutes (GitHub Pages may serve the old index for up to ten more).

A new package also needs its `depictions/<package id>/` folder (the script adds the depiction fields
to every package that has one) and an entry in the home page `index.html`.

Every deb should have `Package`, `Name`, `Version`, `Architecture`, `Description`, `Maintainer`,
`Author` and `Section` in its control file. The script fills `Name`, `Maintainer`, `Author` and
`Section` when an old deb lacks them, but a new build should carry them.

## One-time setup on GitHub

Settings ▸ Pages ▸ Build and deployment ▸ Source: **GitHub Actions**. The result of each run is in
the repository's Actions tab.

## Downloads and ratings

The download counts and star ratings on the package pages were **carried over from YouRepo as of
2026-11-21** and are labelled so. A static source cannot count downloads or collect votes, so these
numbers never change; new downloads and new votes are not counted. The ratings were anonymous star
votes only; YouRepo had no written comments.

## Migration archive

`migration/yourepo/` keeps what was read from the old YouRepo source (`https://imod.yourepo.com`)
before it shuts down: package data, YouRepo's depictions and pages, screenshots and icons.
`migration/generate-depictions.py` is the one-off script that wrote the depictions and the home page
from it; the generated files are meant to be edited by hand from now on.

Third-party package: `com.azzou.rounderls` (RounderLS by Azzou) is included as it is, without a
depiction.
