# Job Scraper

Static job board. `fetch_jobs.py` pulls listings from companies' public ATS APIs
(Greenhouse, Lever, Ashby, SmartRecruiters) into `jobs.json`; `index.html` shows them with
search, source filter, saved jobs and a simple application tracker (stored in your browser).
Applying always happens on the original company page. LinkedIn/Naukri/Indeed are not scraped.

- Edit `companies.json` (`ats` + board `id`), then run `python3 fetch_jobs.py companies.json`.
- Serve locally: `python3 -m http.server` and open http://localhost:8000
- GitHub Actions refreshes `jobs.json` every 6 hours; enable Pages (branch `main`, root) to host.
- Set a real contact email in the `UA` line of `fetch_jobs.py`.
