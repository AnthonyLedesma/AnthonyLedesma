"""Fetch the last year of GitHub contributions for both accounts behind the profile art.

Stdlib only. Needs GITHUB_TOKEN in the environment. Writes art/contrib.json as
{"AnthonyLedesma": <contributionCalendar>, "AnthonyLedesmaTR": <contributionCalendar>}.
Both calendars are public; AnthonyLedesmaTR shows its private (work) contributions as counts only.
"""

import json
import os
import urllib.request
from pathlib import Path

LOGINS = ["AnthonyLedesma", "AnthonyLedesmaTR"]
OUT = Path(__file__).resolve().parent / "contrib.json"
QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { contributionCount contributionLevel date }
        }
      }
    }
  }
}
"""


def calendar(data: dict, login: str) -> dict:
    """The contributionCalendar out of one GraphQL response, or exit on an error."""
    if data.get("errors") or not (data.get("data") or {}).get("user"):
        raise SystemExit(f"GraphQL error for {login}: {json.dumps(data.get('errors'))}")
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def fetch(login: str) -> dict:
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
            "Content-Type": "application/json",
            "User-Agent": "AnthonyLedesma-profile-art",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return calendar(json.load(resp), login)


def main() -> None:
    cals = {login: fetch(login) for login in LOGINS}
    # A token that can't see the work account's private counts returns zero, which
    # would draw an empty layer under a legend that promises one.
    if any(c["totalContributions"] == 0 for c in cals.values()):
        raise SystemExit("an account returned zero contributions")
    OUT.write_text(json.dumps(cals, separators=(",", ":")) + "\n")
    for login, cal in cals.items():
        print(f"{login}: {len(cal['weeks'])} weeks, {cal['totalContributions']} contributions")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
