"""Fetch the last year of GitHub contributions for the profile art.

Stdlib only. Needs GITHUB_TOKEN in the environment. Writes art/contrib.json.
"""

import json
import os
import urllib.request
from pathlib import Path

LOGIN = "AnthonyLedesma"
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


def main() -> None:
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
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
        data = json.load(resp)
    if data.get("errors") or not data.get("data", {}).get("user"):
        raise SystemExit(f"GraphQL error: {json.dumps(data.get('errors'))}")
    OUT.write_text(json.dumps(data, separators=(",", ":")) + "\n")
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    print(f"wrote {OUT.name}: {len(weeks)} weeks")


if __name__ == "__main__":
    main()
