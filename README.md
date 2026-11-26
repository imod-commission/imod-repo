# imod-commission/imod-repo

An APT source for jailbroken iOS, published with Apelin.

Add `https://imod-commission.github.io/imod-repo/` in Irisin.

## How it works

- Packages are the `.deb` files in `debs/`, named
  `<Package>_<Version>_<Architecture>.deb`. Apelin's Distribute… page
  publishes a release build here; a `.deb` pushed by hand works the same.
- On every push to `main`, `.github/workflows/update-repository.yml` runs
  `scripts/update-repository.sh`, which indexes `debs/` into `Packages`,
  `Packages.xz` and `Release`, and publishes the site to GitHub Pages.
  Never commit those indexes or `_site/`.
- `data/release-packages.json` lists packages whose `.deb` stays only on a GitHub
  release (not in `debs/`): the build downloads each, checks its SHA256 and
  points the index at the release asset (`scripts/release-packages.py`).
- `depictions/<package id>/` holds a package's depiction, icon and
  banner; `sileo-featured.json` the banners Irisin shows at the top of the
  source; `CydiaIcon.png`, when present, the source's icon.

Pages may serve the previous index for up to ten minutes after a push.
