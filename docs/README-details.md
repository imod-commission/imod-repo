# imod repo: details

The full notes that used to be the README (layout, adding a version, ratings, downloads, report links, migration). The short README is at the repository root.

APT repository for iOS jailbreak package managers (Sileo, Zebra, Irisin, Cydia…), tweaks by
imod_commission. It is served by GitHub Pages:

**https://imod-commission.github.io/imod-repo/**

## Add the source

- Sileo: open [sileo://source/https://imod-commission.github.io/imod-repo/](sileo://source/https://imod-commission.github.io/imod-repo/)
  or add the URL above by hand in Sources.
- Other package managers: add `https://imod-commission.github.io/imod-repo/` as a source.

The packages here use the real IDs (`com.imodcommission.*`). If you installed them from the old
YouRepo source (`com.yourepo.imod.*`), remove those packages first: the IDs changed, so they
are different packages and would otherwise conflict.

Architectures: `iphoneos-arm`, `iphoneos-arm64` (rootless) and `iphoneos-arm64e` (roothide). Your
package manager shows only the builds that fit your device.

IconSizeFix is offered only as the `iphoneos-arm64` (rootless) build 1.1. There is no RootHide
(`iphoneos-arm64e`) build any more: RootHide users have to convert the rootless package themselves.

## Layout

| Path | What it is |
| --- | --- |
| `debs/` | Every package, one `.deb` each, named `<Package>_<Version>_<Architecture>.deb`. Never edited or rebuilt here. |
| `depictions/<package id>/` | `depiction.json` (native Sileo depiction), `index.html` (web depiction), `icon.png` (the build puts it in the package's `Icon:` field; Sileo shows it, the web pages use it too), `screenshots/` |
| `index.html`, `CydiaIcon.png` | The source's home page and icon. `CydiaIcon.png` (512x512) is the repo icon: the workflow publishes it at the Pages root, where package managers read it, and `index.html` uses it as header image and favicon |
| `assets/repo-source.jpg` | The original image `CydiaIcon.png` was cropped from (not published) |
| `scripts/update-repository.sh` | Builds the site: indexes `debs/` with `apt-ftparchive` into `Packages`, `Packages.gz`, `Packages.xz`, `Release` |
| `scripts/fetch-ratings.py` | At build time: reads the rating issues (open and closed) from the GitHub API and combines them with the carried-over votes in `data/yourepo-baseline.json` into per-package vote counts and means |
| `scripts/fetch-downloads.py` | At build time: reads the GitHub releases of each package's source repo (`data/package-repos.json`) and adds their download counts to the carried-over total |
| `scripts/patch-depictions.py` | At build time: adds the Rating and Downloads rows and the Rate / Report an issue buttons to the **copies** of the depictions in `_site` (the committed files stay as they are) |
| `scripts/close-rating-issues.py` | After the count: thanks and closes each valid rating issue that is still open |
| `data/yourepo-baseline.json` | The numbers carried over from the old source (votes and download totals): the starting values the live numbers are added to |
| `data/package-repos.json` | Per package id: its repository (for release downloads), its `source` (the **Source code** link, added by the build to both depictions; none for HideLSClock, Liquid Glass and RounderLS) and where **Report an issue** goes |
| `.github/ISSUE_TEMPLATE/` | The rating form (`rate-package.yml`), the bug-report form for packages without a tracker of their own (`bug-report.yml`) and the chooser setting (`config.yml`, blank issues off) |
| `data/release-filenames.json` | The explicit overrides: a package version whose index `Filename` is its GitHub release asset instead of `debs/` (checked by size and SHA256 at build time). Currently 26Page 1.0.0 only |
| `scripts/override-filenames.py` | At build time: rewrites the `Filename` of those entries only, and fails the build if the asset is not the file in `debs/` |
| `scripts/check-site-links.py` | Build check: every local `href`/`src` of the home page and the depictions in `_site` must resolve to a file |
| `scripts/inject-metadata.py` | Adds `Depiction`, `SileoDepiction` and `Icon` to each package entry of the index (the old debs do not carry them) and fills a missing `Name`, `Maintainer`, `Author` or `Section` |
| `.github/workflows/update-repository.yml` | On every push to `main`, when a rating issue changes, once a day and by hand: runs the script, closes the counted rating issues and publishes the result to GitHub Pages. Needs `issues: write` |
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
to every package that has one), an entry in the home page `index.html`, its id in the `package`
dropdown of `.github/ISSUE_TEMPLATE/rate-package.yml` (the build warns when that list and `debs/` differ)
and an entry in `data/package-repos.json` (its source repo and where **Report an issue** goes).
Keep the markers `<!--ratings:summary-->`, `<!--ratings:rows-->` and `<!--ratings:links-->` in a
depiction's `index.html` (copy them from another package): that is where the build puts the rating, the
rows and the buttons. Do not write ratings, download counts or report links into the depictions by hand.

Every deb should have `Package`, `Name`, `Version`, `Architecture`, `Description`, `Maintainer`,
`Author` and `Section` in its control file. The script fills `Name`, `Maintainer`, `Author` and
`Section` when an old deb lacks them, but a new build should carry them.

## One-time setup on GitHub

Settings ▸ Pages ▸ Build and deployment ▸ Source: **GitHub Actions**. The result of each run is in
the repository's Actions tab.

Create two labels in Issues ▸ Labels: **`rating`** and **`ignore`**, and a third, **`bug`**, for the bug-report
form. A form can only apply a label that already exists, and without `rating` no vote is counted.

This repository's issue list is for **ratings only** (blank issues are off). Bug reports go to each
tweak's own repository, see below.

## Ratings

**Ratings** are votes cast as GitHub issues, plus the votes carried over from the previous source. A
static site cannot collect votes, so a vote is an issue made with the rating form: *Rate this package*
on a package page (or **New issue ▸ Rate a package** in this repository) opens it with the package
already chosen. Pick 1-5 stars, add an optional comment and submit.

- Ratings are submitted **only** as issues of this repository, with the form. Only issues with the
  `rating` label count, and only a known package id and a rating of 1-5.
- One vote per GitHub account and package: if you rate the same package again, your newest valid
  rating replaces the older one (latest wins). Votes by an account on other packages are separate.
- After the votes are counted, the workflow thanks each valid rating issue with a comment and **closes**
  it (`scripts/close-rating-issues.py`, needs `issues: write`). Closed issues still count, so closing
  changes no number. An older vote that a newer one replaced is closed with a note saying so. An issue
  with the `rating` label that cannot be read (wrong package or rating) is left open with a warning in
  the run's log.
- A vote you want removed (spam, a joke vote): give that issue the **`ignore`** label (or delete the
  issue) and the next build leaves it out.
- The Rating shown is the carried-over votes and the issue votes combined: total votes and their
  weighted mean. The build reads the issues (`scripts/fetch-ratings.py`) and writes the result into the
  site's copies of the depictions only; nothing is committed. A new vote shows after the next deploy, a
  few minutes after the issue is opened (the workflow also runs daily). If GitHub's API cannot be read
  during a build, the pages show the carried-over votes only and the build goes on.
- The carried-over votes (and download totals) are in `data/yourepo-baseline.json`. They were anonymous
  star votes; there were no written comments.

## Downloads

**Downloads** is the number carried over from the previous source (`data/yourepo-baseline.json`) **plus
the download counts of the package's files on GitHub Releases**. It is honest about what that is:

- For each package that has a source repository (`data/package-repos.json`), `scripts/fetch-downloads.py`
  reads that repository's releases with the workflow's `GITHUB_TOKEN` and adds up `download_count` of
  every release asset named `<package id>_*.deb` (all releases, all versions). That counts how often
  the release **files** were downloaded from GitHub, by anyone: package managers installing from
  this source, which is served by GitHub Pages, are **not** counted, because Pages has no counter.
- Packages without a source repository (HideLSClock, Liquid Glass) show the carried-over total only,
  and it does not grow.
- If a repository's releases cannot be read (network, rate limit), that package falls back to the
  carried-over number and the build warns and goes on.
- The release files are the same bytes as the matching files in `debs/` (checked 2026-11-21 for 26Page,
  Ersatz, Griddy, IconSizeFix, MoveSleepAlarm, Nig and notifyyy). The carried-over totals come from the
  previous source's own hosting, not from GitHub, so the two are separate downloads and are added.
  The IconSizeFix release also carries an older `0.1.0` file that is no longer in `debs/`; its
  downloads are counted too.

## Download test (release-asset Filename)

Only 26Page 1.0.0 (`iphoneos-arm64`) uses this for now, listed in `data/release-filenames.json`. Its index
entry's `Filename` is the GitHub release asset `https://github.com/imod-commission/26Page/releases/download/1.0/com.imodcommission.26page_1.0.0_iphoneos-arm64.deb`
instead of `debs/...`. The asset is the same file as `debs/` (the build checks size and SHA256 and fails
if they differ). Size, SHA256 and the other fields are unchanged. Every other package stays on `debs/`.

- Sileo is meant to download that `.deb` from the GitHub release, so GitHub counts those downloads
  (they are part of 26Page's Downloads).
- A direct download from the release page is counted too: GitHub cannot tell the two apart.
- Whether Sileo accepts an absolute `Filename` is **untested**. It is confirmed only when someone adds this
  source and installs 26Page from it. If Sileo refuses it, delete the entry in `data/release-filenames.json`;
  the next build puts the package back on `debs/`.

## Report an issue

Each package page has a **Report an issue** button (native Sileo depiction and web page) that opens the
tweak's **own** GitHub issue tracker, from the map in `data/package-repos.json`:

| Package | Report an issue goes to |
| --- | --- |
| 26Page, Ersatz, IconSizeFix, MoveSleepAlarm, notifyyy, Nig | `https://github.com/imod-commission/<repo>/issues/new` of the tweak's repository |
| Griddy | this repository's bug-report form (`imod-commission/griddy` is a fork with Issues turned off) |
| HideLSClock, Liquid Glass | this repository's bug-report form (`bug-report.yml`, label `bug`): they have no repository |
| RounderLS (third party) | no button |

Every repository in the map was checked against the GitHub API. To move a package to its own tracker
later, set its `report` to `"repo"` in `data/package-repos.json` (for Griddy: enable Issues in that
repository first).

## Migration archive

`migration/yourepo/` keeps what was read from the old YouRepo source (`https://imod.yourepo.com`)
before it shuts down: package data, YouRepo's depictions and pages, screenshots and icons.
`migration/generate-depictions.py` is the one-off script that wrote the depictions and the home page
from it; the generated files are meant to be edited by hand from now on.

Third-party package: `com.azzou.rounderls` (RounderLS by Azzou) is included as it is. It has a
plain depiction page that says it is not by imod_commission, and no report button.

Icons: the packages' icons (`depictions/<id>/icon.png`) are YouRepo's generic default icons, copied from
`migration/yourepo/assets/` (`yourepo-user33.png`, the drill, for tweaks; `yourepo-user31.png`, the monitor,
for the theme). Ersatz and Nig have their own icons. RounderLS had no icon on YouRepo and has none here.
