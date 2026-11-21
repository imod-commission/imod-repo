# YouRepo migration archive

Raw data scraped from the old YouRepo source (https://imod.yourepo.com) on 2026-11-21,
kept because YouRepo is being shut down. Reference only: nothing in this folder is
published on the site or used by the build.

- `migration.json`: per YouRepo package: name, version, section, description, author, downloads,
  rating, rating count, published date, screenshot URLs, changelog.
- `<name>.json`: YouRepo's native depiction for that package (contains YouRepo ads and buttons,
  not reused). `<name>.html`: its web page.
- `Packages`, `Release`: YouRepo's old APT index. Its package IDs are `com.yourepo.imod.*`, which are
  not the real IDs (`com.imodcommission.*`).
- `assets/`: screenshots and icons. `yourepo-user31.png` and `yourepo-user33.png` are YouRepo's
  generic default icons, `repo-CydiaIcon.png` is YouRepo's source icon.
- The author e-mail address was removed from `migration.json` and `Packages`.
