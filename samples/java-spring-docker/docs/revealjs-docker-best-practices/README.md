# Reveal.js presentation

This folder contains a Reveal.js presentation for the current Java/Spring Dockerfile best practices.

## Open locally

```bash
cd /path/to/your-java25-project
python3 -m http.server 8000
```

Then open:

- `http://localhost:8000/docs/revealjs-docker-best-practices/`

## Files

- `index.html`: slide deck
- `assets/custom.css`: minimal style tweaks

## Notes

- Reveal.js is loaded from CDN (no npm setup required).
- The deck references deep-dive content under `benchmarks/*/DEEP_DIVE.md` and AOT docs in `benchmarks/05-jep483-aot-cache/`.

