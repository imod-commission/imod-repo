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

IconSizeFix is offered only as the `iphoneos-arm64` (rootless) build 1.1. There is no RootHide
(`iphoneos-arm64e`) build any more: RootHide users have to convert the rootless package themselves.

## Layout

| Path | What it is |
| --- | --- |
| `debs/` | Every package, one `.deb` each, named `<Package>_<Version>_<Architecture>.deb`. Never edited or rebuilt here. |
| `depictions/<package id>/` | `depiction.json` (native Sileo depiction), `index.html` (web depiction), `icon.png`, `screenshots/` |
| `index.html`, `CydiaIcon.png` | The source's home page and icon |
| `scripts/update-repository.sh` | Builds the site: indexes `debs/` with `apt-ftparchive` into `Packages`, `Packages.gz`, `Packages.xz`, `Release` |
| `scripts/fetch-ratings.py` | At build time: reads the rating issues from the GitHub API and combines them with `data/yourepo-baseline.json` into per-package vote counts and means |
| `scripts/patch-depictions.py` | At build time: adds the rating, the Downloads row and the Rate / Report buttons to the **copies** of the depictions in `_site` (the committed files stay as they are) |
| `data/yourepo-baseline.json` | The frozen YouRepo votes and download counts: the only place the Downloads rows are read from |
| `.github/ISSUE_TEMPLATE/` | The rating form (`rate-package.yml`) and the issue chooser setting (`config.yml`) |
| `scripts/inject-metadata.py` | Adds `Depiction`, `SileoDepiction` and `Icon` to each package entry of the index (the old debs do not carry them) and fills a missing `Name`, `Maintainer`, `Author` or `Section` |
| `.github/workflows/update-repository.yml` | On every push to `main`, when a rating issue changes, once a day and by hand: runs the script and publishes the result to GitHub Pages |
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
to every package that has one), an entry in the home page `index.html`, and its id in the `package`
dropdown of `.github/ISSUE_TEMPLATE/rate-package.yml` (the build warns when that list and `debs/` differ).
Keep the markers `<!--ratings:summary-->`, `<!--ratings:rows-->` and `<!--ratings:links-->` in a
depiction's `index.html` (copy them from another package): that is where the build puts the rating, the
rows and the buttons. Do not write ratings or download counts into the depictions by hand.

Every deb should have `Package`, `Name`, `Version`, `Architecture`, `Description`, `Maintainer`,
`Author` and `Section` in its control file. The script fills `Name`, `Maintainer`, `Author` and
`Section` when an old deb lacks them, but a new build should carry them.

## One-time setup on GitHub

Settings ▸ Pages ▸ Build and deployment ▸ Source: **GitHub Actions**. The result of each run is in
the repository's Actions tab.

Create two labels in Issues ▸ Labels: **`rating`** and **`ignore`**. The rating form can only apply a
label that already exists, and without `rating` no vote is counted.

## Ratings and downloads

**Ratings** are the old YouRepo votes plus votes from GitHub issues. A static site cannot collect votes,
so a vote is an issue made with the rating form: *Rate this package* on a package page (or **New issue ▸
Rate a package** in this repository) opens it with the package already chosen. Pick 1-5 stars, add an
optional comment and submit.

- One vote per GitHub account and package: if you rate the same package again, your newest valid rating
  replaces the older one. Votes by an account on other packages are separate.
- Only issues with the `rating` label count, and only a known package id and a rating of 1-5. Closed
  issues still count.
- A vote you want removed (spam, a joke vote): give that issue the **`ignore`** label (or delete the
  issue) and the next build leaves it out.
- The Rating shown is (YouRepo votes + issue votes) combined: total votes and their weighted mean. The
  build reads the issues (`scripts/fetch-ratings.py`) and writes the result into the site's copies of the
  depictions only; nothing is committed. A new vote shows after the next deploy, a few minutes after the
  issue is opened (the workflow also runs daily). If GitHub's API cannot be read during a build, the page
  shows the YouRepo numbers only and the build goes on.
- The YouRepo votes (and the download counts) are in `data/yourepo-baseline.json`. Their votes were
  anonymous star votes; YouRepo had no written comments.

**Downloads** are a frozen YouRepo number: the Downloads row reads "Downloads (YouRepo, as of
2026-11-21)" and never changes, because a static source cannot count downloads. It is read from
`data/yourepo-baseline.json`, the only place the number lives.

Comments and bug reports are ordinary issues (**Report an issue / comment** on each page).

## Migration archive

`migration/yourepo/` keeps what was read from the old YouRepo source (`https://imod.yourepo.com`)
before it shuts down: package data, YouRepo's depictions and pages, screenshots and icons.
`migration/generate-depictions.py` is the one-off script that wrote the depictions and the home page
from it; the generated files are meant to be edited by hand from now on.

Third-party package: `com.azzou.rounderls` (RounderLS by Azzou) is included as it is, without a
depiction.
