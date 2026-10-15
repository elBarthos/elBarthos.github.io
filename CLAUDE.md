# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Personal portfolio site for Tobias Barth, deployed via GitHub Pages at https://elBarthos.github.io (the repo is `elBarthos.github.io`, so `main` is published directly). Content is in German. There is no build step, package manager, linter, or test suite — just static files. To preview, open the HTML files in a browser or run `python3 -m http.server` in the repo root.

## Structure

- `index.html` — single-page portfolio (sections: hero, about, skills, projects, contact; nav labels and headings are German, lowercase). All CSS is inline in a `<style>` block (dark theme driven by CSS variables in `:root`) and all JS is inline at the bottom of the file.
- `cv.html` — standalone, separately styled CV page (different fonts and design than `index.html`). It has `@media print` / `@page` A4 rules, so it doubles as the source for printing to PDF. Both A4 pages (`.page`, fixed 297mm height) are completely full: overflowing content silently disappears behind the page-1 footer band or the page-2 footer, so render and check after any CV text change. Skills are kept identical between `index.html` and `cv.html`.
- `img/` — images and video. Project screenshots for the VR game live in `img/vr_lernspiel/`.

## Things that span the code

- **Project details use modals.** Each project card in `#projects` opens a `.modal-backdrop` (`#modal-robo`, `#modal-fotobox`, `#modal-vr`) via `openModal(id)` / `closeModal(id)`. Adding a project means adding both a card and a matching modal.
- **Scroll animations:** elements with class `.reveal` get `.visible` added by an `IntersectionObserver`.
- **External dependencies:** only Google Fonts (and the YouTube embed). Open Graph / meta description tags in `<head>` of `index.html` should be kept in sync with the hero text; `img/og-image.jpg`, `img/favicon.svg` and `img/apple-touch-icon.png` belong to them.
- **`cv.html` embeds its photos as base64 JPEG** so the file works standalone; keep them small (400px head photo, 120px avatar).
- **Cross-links use absolute URLs** (`https://elBarthos.github.io/cv.html`), not relative paths.

## Images

Pages reference optimized `.webp` files; the original `.png` files are kept alongside them in the repo (e.g. `img/foto.png` + `img/foto.webp`, and the full-size PNGs in `img/vr_lernspiel/`). When adding images, commit a compressed WebP for use in the HTML (use `loading="lazy"` as the existing markup does) and avoid large PNGs. Prefer filenames without spaces or umlauts.
