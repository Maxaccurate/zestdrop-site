# zestdrop.org

Static website for [ZestDrop](https://github.com/Maxaccurate/ZestDrop). No build step: plain HTML, CSS and JavaScript.

- `index.html` holds the English copy (what search engines see).
- `assets/js/i18n.js` holds the Chinese copy and the demo strings. Every `data-i18n` key in the HTML needs a matching Chinese entry.
- `assets/js/site.js` runs the language switch, reads the latest release from the GitHub API to keep the download button current, and powers the drag-to-convert demo.

Preview locally with `python -m http.server 8765` in this folder, then open http://localhost:8765.

When you change a CSS or JS file, bump its `?v=` number in `index.html` (and `404.html` for the stylesheet) so visitors don't get a stale cached copy.

## Testing the demo

`tests/demo-tests.js` drives the drag-to-convert demo with pointer and keyboard events (21 checks: conversions, the job queue, cancelling with Esc, alt-tab or a missed release, keyboard use, language switching and layout). With the site running locally, open http://localhost:8765/?lang=en, paste the file into the browser console, and wait about 40 seconds for the summary. Synthetic events can't reproduce every browser quirk, so also try a few drags with a real mouse.

## File-type showcase and the two numbers

The Features section has two stat cards and a tabbed showcase (`assets/js/showcase.js`), whose wheels are drawn live from option lists that mirror the app's `Catalog.cs`. `/?tab=video` opens a given tab (images, video, audio, documents, archives).

The numbers are counted, not estimated, so recount them when the catalog changes:

- **333 conversion options** = input-to-output format pairs across the app's 49 input formats, 145 of them Office conversions that need desktop Office. Non-Office pairs were checked against the app's own `--capabilities` output.
- **27 advanced file tools** = the tool definitions in `Catalog.cs`.

`tests/showcase-tests.js` (10 checks) covers this section; run it the same way as `tests/demo-tests.js`.
