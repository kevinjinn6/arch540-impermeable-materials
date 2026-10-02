"""
Smoke test for the map's data files. Standard library only, so it runs
anywhere, including in the GitHub Pages workflow before a deploy.

    python3 map/check_data.py

Checks that map/data/lots.geojson has the shape the page expects, that the
figures the README quotes still hold, and that map/data/roof-walls.json (if
present) is consistent with it. Exit code 0 = fine, 1 = something is off.
"""

import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOTS = HERE / "data" / "lots.geojson"
WALLS = HERE / "data" / "roof-walls.json"

# What the README and the page's notes say about the published snapshot.
# Update these when the data is regenerated (buildings.py prints them).
EXPECT = {
    "features": 63031,
    "in_scope": 62248,
    "median_site_m2": 403.02,
    "over_50_roof_edge": 13594,
    "over_75_roof_edge": 16,
    "example": {"address": "3528 W 30TH AV", "A": 602.04, "r": 280.40},
}
EXPECT_WALLS = {"eave_m": 0.45, "over_50_walls": 777, "over_75_walls": 4,
                "example_rw": 237.22}

problems = []


def check(ok, msg):
    if not ok:
        problems.append(msg)
    print(("  ok   " if ok else "  FAIL ") + msg)


def main():
    print(f"Checking {LOTS.relative_to(HERE.parent)}")
    data = json.load(open(LOTS, encoding="utf-8"))
    check(data.get("type") == "FeatureCollection", "a FeatureCollection")
    feats = data.get("features", [])
    check(len(feats) == EXPECT["features"], f"{len(feats):,} features (expected {EXPECT['features']:,})")
    need = {"k", "ad", "A", "r", "sc"}
    missing = [f for f in feats if not need <= set(f["properties"])]
    check(not missing, f"every feature has {sorted(need)} ({len(missing)} missing)")
    keys = [f["properties"]["k"] for f in feats]
    check(len(set(keys)) == len(keys), "site keys are unique")
    bad_sc = [f for f in feats if f["properties"]["sc"] not in (0, 1, 2)]
    check(not bad_sc, "sc is 0, 1 or 2 everywhere")
    bad_area = [f for f in feats if not (isinstance(f["properties"]["A"], (int, float)) and f["properties"]["A"] > 0)]
    check(not bad_area, "site areas are positive numbers")
    bad_roof = [f for f in feats if f["properties"]["r"] < 0]
    check(not bad_roof, "roof areas are not negative")
    ins = [f["properties"] for f in feats if f["properties"]["sc"] == 0]
    check(len(ins) == EXPECT["in_scope"], f"{len(ins):,} ordinary lots (expected {EXPECT['in_scope']:,})")
    med = statistics.median(p["A"] for p in ins)
    check(abs(med - EXPECT["median_site_m2"]) < 0.01, f"median ordinary site {med:.2f} m²")
    o50 = sum(p["r"] > 0.5 * p["A"] for p in ins)
    o75 = sum(p["r"] > 0.75 * p["A"] for p in ins)
    check(o50 == EXPECT["over_50_roof_edge"], f"{o50:,} ordinary sites over 50% to the roof edge")
    check(o75 == EXPECT["over_75_roof_edge"], f"{o75:,} ordinary sites over 75% to the roof edge")
    ex = EXPECT["example"]
    hit = [p for p in ins if p["ad"] == ex["address"]]
    check(len(hit) == 1 and abs(hit[0]["A"] - ex["A"]) < 0.01 and abs(hit[0]["r"] - ex["r"]) < 0.01,
          f"{ex['address']}: A {ex['A']} m², roof {ex['r']} m²")
    geoms = {f["geometry"]["type"] for f in feats}
    check(geoms <= {"Polygon", "MultiPolygon"}, f"geometries are polygons ({', '.join(sorted(geoms))})")

    if WALLS.exists():
        print(f"Checking {WALLS.relative_to(HERE.parent)}")
        w = json.load(open(WALLS, encoding="utf-8"))
        check(abs(w.get("eave_m", -1) - EXPECT_WALLS["eave_m"]) < 1e-9, f"eave allowance {w.get('eave_m')} m")
        rw = w.get("rw", {})
        check(set(rw) == set(keys), "one rw per site, same keys as lots.geojson")
        bigger = [k for k, f in zip(keys, feats) if rw.get(k, 0) > f["properties"]["r"] + 0.011]
        check(not bigger, f"rw never exceeds r ({len(bigger)} do)")
        w50 = sum(rw[p["k"]] > 0.5 * p["A"] for p in ins)
        w75 = sum(rw[p["k"]] > 0.75 * p["A"] for p in ins)
        check(w50 == EXPECT_WALLS["over_50_walls"], f"{w50:,} ordinary sites over 50% to the walls")
        check(w75 == EXPECT_WALLS["over_75_walls"], f"{w75:,} ordinary sites over 75% to the walls")
        if hit:
            check(abs(rw.get(hit[0]["k"], 0) - EXPECT_WALLS["example_rw"]) < 0.01,
                  f"{ex['address']}: roof to the walls {EXPECT_WALLS['example_rw']} m²")
    else:
        print(f"  note {WALLS.name} not present; the page will use roof-edge areas and say so")

    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print("  -", p)
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
