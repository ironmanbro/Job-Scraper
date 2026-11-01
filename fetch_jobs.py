#!/usr/bin/env python3
"""Fetch jobs from companies' public ATS APIs (Greenhouse, Lever, Ashby, SmartRecruiters).

Usage: python3 fetch_jobs.py companies.json [-o jobs.json]
companies.json: [{"name": "Acme", "ats": "greenhouse", "id": "acme"}, ...]
Only documented public endpoints are used. Not for LinkedIn/Naukri/Indeed.
"""
import argparse, json, sys, time, urllib.request, urllib.parse
from datetime import datetime, timezone

UA = "JobHubBot/0.1 (+contact: set-your-email@example.com)"  # set a real contact
DELAY = 1.0  # seconds between requests, be polite


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def iso_ms(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat() if ms else None


def greenhouse(c):
    d = get(f"https://boards-api.greenhouse.io/v1/boards/{c['id']}/jobs?content=true")
    for j in d.get("jobs", []):
        yield dict(job_id=str(j["id"]), title=j["title"], location=(j.get("location") or {}).get("name"),
                   url=j["absolute_url"], posted=j.get("updated_at"), description=j.get("content"))


def lever(c):
    for j in get(f"https://api.lever.co/v0/postings/{c['id']}?mode=json"):
        cat = j.get("categories") or {}
        yield dict(job_id=j["id"], title=j["text"], location=cat.get("location"), url=j["hostedUrl"],
                   posted=iso_ms(j.get("createdAt")), description=j.get("descriptionPlain"))


def ashby(c):
    d = get(f"https://api.ashbyhq.com/posting-api/job-board/{c['id']}")
    for j in d.get("jobs", []):
        yield dict(job_id=j["id"], title=j["title"], location=j.get("location"), url=j.get("jobUrl"),
                   posted=j.get("publishedAt"), description=j.get("descriptionPlain"))


def smartrecruiters(c):
    offset = 0
    while True:
        d = get(f"https://api.smartrecruiters.com/v1/companies/{c['id']}/postings?limit=100&offset={offset}")
        for j in d.get("content", []):
            loc = j.get("location") or {}
            yield dict(job_id=j["id"], title=j["name"],
                       location=", ".join(x for x in (loc.get("city"), loc.get("country")) if x),
                       url=f"https://jobs.smartrecruiters.com/{c['id']}/{j['id']}",
                       posted=j.get("releasedDate"), description=None)
        offset += 100
        if offset >= d.get("totalFound", 0):
            break
        time.sleep(DELAY)


ADAPTERS = {"greenhouse": greenhouse, "lever": lever, "ashby": ashby, "smartrecruiters": smartrecruiters}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("companies")
    ap.add_argument("-o", "--out", default="jobs.json")
    a = ap.parse_args()
    companies = json.load(open(a.companies))
    jobs, seen, errors = [], set(), []
    fetched_at = datetime.now(timezone.utc).isoformat()
    for c in companies:
        fn = ADAPTERS.get(c.get("ats"))
        if not fn:
            errors.append(f"{c.get('name')}: unsupported ats '{c.get('ats')}'")
            continue
        try:
            n = 0
            for j in fn(c):
                key = (c["ats"], c["id"], j["job_id"])
                if key in seen:
                    continue
                seen.add(key)
                jobs.append({**j, "company": c["name"], "source": c["ats"],
                             "source_label": f"{c['name']} careers ({c['ats']})", "fetched_at": fetched_at})
                n += 1
            print(f"{c['name']}: {n} jobs", file=sys.stderr)
        except Exception as e:  # one failing company must not stop the run
            errors.append(f"{c['name']}: {e}")
        time.sleep(DELAY)
    json.dump(jobs, open(a.out, "w"), indent=1, ensure_ascii=False)
    print(f"Wrote {len(jobs)} jobs to {a.out}", file=sys.stderr)
    for e in errors:
        print("ERROR", e, file=sys.stderr)


if __name__ == "__main__":
    main()
