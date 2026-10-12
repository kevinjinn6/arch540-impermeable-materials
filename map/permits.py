"""
================================================================================
 LOTS BUILT ON SINCE THE ROOF DATA  --  writes map/data/permits.json
================================================================================

WHY THIS EXISTS
  The map's roofs are the City's 2015 air-photo footprints, and nothing newer
  exists as outlines. A lot where the City has since issued a permit for a
  new building or a demolition very likely has different roofs today, so the
  page flags it: "the 2015 roofs may be out of date". The figures are NOT
  changed; the flag only tells the reader which lots to doubt.

WHAT IT READS
  City of Vancouver open data, "Issued building permits" (all permits issued
  since 2017-01-01; 2015 and 2016 are not in it), downloaded fresh, and
  map/data/lots.geojson.

WHAT IT KEEPS
  Permits whose type of work is in TYPES_OF_WORK: a new building (a house, a
  laneway house, a duplex...) or a demolition. "Addition / Alteration" is left
  out: most are interior work, suites or solar panels, which do not change a
  roof outline, and flagging them would flag lots that have not changed.

HOW A PERMIT FINDS ITS LOT
  1. By address: the permit's street address (the part before the first
     comma, without a "#3" unit), written the way the lots are (AVENUE -> AV,
     STREET -> ST), against the lot's address.
  2. Otherwise by place, only for a lot with no civic address: the point the
     City geocoded the permit to, inside that lot. (Checked 2026-10-11: of the
     915 permits whose point falls inside a lot with ANOTHER address, 713 were
     next door on the same street, e.g. 646 E 23rd inside 648 E 23rd: the
     geocoder's point, not the permit's lot. Those are left out.)
  Permits that find no R1-1 lot (most are in other zones) are left out.

WHAT IT WRITES
  {"source": ..., "retrieved": "2026-10-11", "since": "2017-01-01",
   "lots": {"R11-000123": [["2019-06-14", "new", "Laneway House"], ...]}}
  one list per lot, oldest first: issue date, "new" or "demo", and the City's
  use category (empty for a demolition).

HOW TO RUN IT
     source .venv/bin/activate          (the geopandas environment)
     python map/permits.py
  Downloads about 19,000 permits (a few MB, one request, no API key) and takes
  under a minute. Re-run to bring the flags up to date.
================================================================================
"""

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely

# ==============================================================================
#  CONFIGURATION
# ==============================================================================
DATASET = "issued-building-permits"
EXPORT = f"https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/{DATASET}/exports/json"
TYPES_OF_WORK = {"New Building": "new", "Demolition / Deconstruction": "demo"}
SINCE = "2017-01-01"          # the dataset's first issue date
# The lots spell these street types short; the permits spell them out.
STREET_TYPES = {"AVENUE": "AV", "STREET": "ST"}
UTM10N = 26910
HERE = Path(__file__).resolve().parent
LOTS = HERE / "data" / "lots.geojson"
OUT = HERE / "data" / "permits.json"
# ==============================================================================


def normalise(address):
    """The page's address form: upper case, no punctuation, single spaces."""
    return " ".join(re.sub(r"[.,]", " ", str(address or "").upper()).split())


def permit_address(raw):
    """'1948 E 33RD AVENUE #3, Vancouver, BC V5N 3E4' -> '1948 E 33RD AV'."""
    street = str(raw or "").split(",")[0]
    street = re.sub(r"#\s*\S+", "", street)            # a unit: "#3", "# 101"
    words = normalise(street).split()
    if words and words[-1] in STREET_TYPES:
        words[-1] = STREET_TYPES[words[-1]]
    return " ".join(words)


def download():
    where = " or ".join(f'typeofwork="{t}"' for t in TYPES_OF_WORK)
    q = urllib.parse.urlencode({"select": "permitnumber,issuedate,typeofwork,address,specificusecategory,geo_point_2d",
                                "where": where})
    print(f"Downloading {DATASET} ({', '.join(TYPES_OF_WORK)})…", flush=True)
    with urllib.request.urlopen(f"{EXPORT}?{q}", timeout=300) as r:
        rows = json.load(r)
    print(f"  {len(rows):,} permits")
    return rows


def main():
    rows = download()
    lots = gpd.read_file(LOTS)
    by_address = {}
    for k, ad in zip(lots["k"], lots["ad"]):
        if ad:
            by_address.setdefault(normalise(ad), k)

    found, how = {}, {"address": 0, "place": 0, "none": 0}
    unplaced = []
    for p in rows:
        k = by_address.get(permit_address(p["address"]))
        if k:
            how["address"] += 1
            found.setdefault(k, []).append(p)
        else:
            unplaced.append(p)
    # By place, for the rest: the permit's point inside a lot.
    pts = [p for p in unplaced if p.get("geo_point_2d")]
    if pts:
        g = gpd.GeoDataFrame({"i": range(len(pts))},
                             geometry=[shapely.Point(p["geo_point_2d"]["lon"], p["geo_point_2d"]["lat"]) for p in pts],
                             crs=4326)
        no_address = lots[lots["ad"].fillna("") == ""][["k", "geometry"]]
        hit = gpd.sjoin(g, no_address, how="inner", predicate="within")
        for i, k in zip(hit["i"], hit["k"]):
            how["place"] += 1
            found.setdefault(k, []).append(pts[i])
    how["none"] = len(rows) - how["address"] - how["place"]

    out = {}
    for k, ps in found.items():
        seen = set()
        items = []
        for p in sorted(ps, key=lambda p: p["issuedate"] or ""):
            if p["permitnumber"] in seen or not p["issuedate"]:
                continue
            seen.add(p["permitnumber"])
            use = p.get("specificusecategory") or []
            use = use[0] if isinstance(use, list) and use else (use if isinstance(use, str) else "")
            kind = TYPES_OF_WORK[p["typeofwork"]]
            items.append([p["issuedate"][:10], kind, use if kind == "new" else ""])
        if items:
            out[k] = items
    doc = {"source": f"City of Vancouver open data, {DATASET}", "retrieved": time.strftime("%Y-%m-%d"),
           "since": SINCE, "types_of_work": list(TYPES_OF_WORK), "n": len(out), "lots": dict(sorted(out.items()))}
    OUT.write_text(json.dumps(doc, separators=(",", ":")))
    print(f"  matched by address {how['address']:,}, by place {how['place']:,}, no R1-1 lot {how['none']:,}")
    print(f"  {len(out):,} lots with a new-building or demolition permit -> {OUT.relative_to(HERE.parent)} "
          f"({OUT.stat().st_size / 1e3:.0f} KB)")


if __name__ == "__main__":
    sys.exit(main())
