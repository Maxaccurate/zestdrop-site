# zestdrop.org

Static website for [ZestDrop](https://github.com/Maxaccurate/ZestDrop). No build step: plain HTML, CSS and JavaScript.

- `index.html` holds the English copy (what search engines see).
- `assets/js/i18n.js` holds the Chinese copy and the demo strings. Every `data-i18n` key in the HTML needs a matching Chinese entry.
- `assets/js/catalog.js` holds the app's real wheel menus (every format and tool, labelled in English and Chinese) and the two counts on the page. It is generated, never edited by hand; see below.
- `assets/js/site.js` runs the language switch, reads the latest release from the GitHub API to keep the download button current, and powers the drag-to-convert demo.
- `assets/js/wheel-ui.js` draws the shared rounded faces, raised sidewalls and hub for both the demo and showcase. Its geometry mirrors `DropWheel.Keycap` in the app's `FloatingWheel.cs` (outer radius 172, inner dead zone 65). Keep it in sync when the app's wheel changes; hit testing uses the actual rounded face, not an approximate wedge.

Preview locally with `python -m http.server 9876` in this folder, then open http://localhost:9876. (Cloudflare Pages serves `privacy.html` as `/privacy`; the local server needs the `.html`.)

When you change a CSS or JS file, bump its `?v=` number in `index.html` (and `404.html` for the stylesheet) so visitors don't get a stale cached copy.

## Testing the demo

`tests/demo-tests.js` drives the drag-to-convert demo with pointer and keyboard events (21 checks: conversions, the job queue, cancelling with Esc, alt-tab or a missed release, keyboard use, language switching and layout). With the site running locally, open http://localhost:9876/?lang=en, paste the file into the browser console, and wait about 40 seconds for the summary. Synthetic events can't reproduce every browser quirk, so also try a few drags with a real mouse.

## Microsoft Store link

The hero and the download section link to the Store listing, product ID **9NG514X8RQC6** (`https://apps.microsoft.com/detail/9NG514X8RQC6?mode=direct`, the link form Microsoft's badge generator uses). The badges in `assets/img/store/` are Microsoft's official "Download from the Microsoft Store" badges from `get.microsoft.com/images/`, in English and Chinese, black for light pages and white for dark ones. They are stored here rather than loaded from Microsoft, so visitors' browsers contact Microsoft only when they click. Microsoft's badge guidelines allow resizing but not recolouring or cropping them.

## After each app release

1. **Menus and numbers.** Run `python scripts/build-catalog.py --app <ZestDrop.exe> --catalog-source <ZestDrop/work/ZestDrop/Catalog.cs>`. It asks the app (`--capabilities`) for the menus of one sample of every file type, in both languages, and rewrites `assets/js/catalog.js`. Run it on a PC with desktop Office installed (Office conversions only appear then), with the combined-tools layout selected, and check its warnings. Saved flows are left out automatically.
2. **The two stat cards** in `index.html` (and their Chinese descriptions in `i18n.js`) must match `counts` in `catalog.js`; `tests/showcase-tests.js` fails if they don't. For v1.0.0: **341 conversion options** (input-to-output format pairs across 50 input formats, 145 of them Office conversions that need desktop Office) and **46 tools** (every tool the app defines; combined entries such as Crop & rotate are not counted twice).
3. **Screenshots**, then version, download size and requirements in `index.html`, `i18n.js` and the fallback in `site.js`, and anything the release notes change about privacy (`privacy.html`).

## File-type showcase

The Features section has two stat cards and a tabbed showcase (`assets/js/showcase.js`). Each tab shows the app's menus for one sample file (JPG, MP4, WAV, PDF, a folder) straight from `catalog.js`. `/?tab=video` opens a given tab (images, video, audio, documents, archives).

`tests/showcase-tests.js` (11 checks, including one that compares every tab with the app's menus in both languages) covers this section; run it the same way as `tests/demo-tests.js`.

`tests/wheel-ui-tests.js` (6 checks) covers the rounded geometry for 0, 1, 4, 6, 7, 8, 9 and 10 options: face/sidewall pairing, correct petal centres, the hub dead zone, gaps, rounded-off corners and selection styling. Also test native mouse drags on a face and in a gap, and touch taps in the showcase.

## Refreshing screenshots

The website images are real renders of the app, not recreated UI. `scripts/refresh-screenshots.py` captures the format wheel, the tool wheel, the combined Crop & rotate window and the progress cards in English and Chinese, and rebuilds the social-share preview. The combined window has no render mode in the app, so `scripts/capture-window.ps1` opens it briefly and captures it with Windows' PrintWindow. It requires Pillow, PowerShell 7 (`pwsh`, which captures at full resolution) and a current portable app build, on a display scaled to 150% or more. Pass `--app <ZestDrop.exe>`, `--video <sample.mp4>`, `--image <sample.png/jpg>` and `--render-dir <scratch folder>`. It opens and closes tool windows, writes intermediates only to the supplied scratch folder, and updates `assets/img`; it does not change the app repository.

After refreshing, bump image query versions in `index.html` as well as CSS/JS versions so visitors fetch the new assets.
