"""Task generation + goal predicates.

Five workflow families (airline/retail, tau^3-bench shape):
  oneway    — book + confirm + pay one flight
  roundtrip — book + confirm + pay outbound AND return, SAME airline
              (the coordination constraint the myopic baseline misses)
  single    — order + pay + ship one product
  bundle    — order with TWO items from the SAME warehouse, pay + ship
              (the coordination constraint the myopic baseline misses)
  modify    — book a flight, then modify to a DIFFERENT flight, confirm+pay

Each task carries a world seed so every arm replays the identical world.
Worlds are fresh per task, so goal predicates are existence checks over
final state only.
"""

from __future__ import annotations

import random

from .world import ROUTES, DATES, CATEGORIES, PASSENGER


def generate_tasks(n, seed):
    rng = random.Random(seed)
    tasks = []
    families = ["oneway"] * 20 + ["roundtrip"] * 25 + ["single"] * 15 \
        + ["bundle"] * 25 + ["modify"] * 15
    for i in range(n):
        fam = families[i % len(families)]
        route = ROUTES[rng.randrange(len(ROUTES))]
        date = DATES[rng.randrange(len(DATES))]
        t = {"id": i, "family": fam, "world_seed": seed * 100000 + i,
             "origin": route[0], "dest": route[1], "date": date,
             "passenger": PASSENGER}
        if fam == "roundtrip":
            t["ret_date"] = DATES[1 - DATES.index(date)]
        if fam in ("single", "bundle"):
            t["query"] = CATEGORIES[rng.randrange(len(CATEGORIES))]
            t["qty"] = rng.randint(1, 2)
        if fam == "bundle":
            t["query2"] = CATEGORIES[rng.randrange(len(CATEGORIES))]
            t["qty2"] = rng.randint(1, 2)
        tasks.append(t)
    return tasks


def _paid(world, bid):
    return any(p["ref_id"] == bid for p in world.payments.values())


def make_goal(task):
    fam = task["family"]

    def goal(world):
        if fam == "oneway":
            for bid, bk in world.bookings.items():
                if bk["status"] != "confirmed" or not _paid(world, bid):
                    continue
                fl = world.flights[bk["flight_id"]]
                if (fl["origin"], fl["dest"], fl["date"]) == \
                        (task["origin"], task["dest"], task["date"]):
                    return True
            return False
        if fam == "roundtrip":
            outs, rets = set(), set()
            for bid, bk in world.bookings.items():
                if bk["status"] != "confirmed" or not _paid(world, bid):
                    continue
                fl = world.flights[bk["flight_id"]]
                if (fl["origin"], fl["dest"], fl["date"]) == \
                        (task["origin"], task["dest"], task["date"]):
                    outs.add(fl["airline"])
                if (fl["origin"], fl["dest"], fl["date"]) == \
                        (task["dest"], task["origin"], task["ret_date"]):
                    rets.add(fl["airline"])
            return len(outs & rets) > 0
        if fam == "single":
            for oid, od in world.orders.items():
                if od["status"] == "shipped" and len(od["items"]) == 1 \
                        and _paid(world, oid):
                    return True
            return False
        if fam == "bundle":
            for oid, od in world.orders.items():
                if od["status"] == "shipped" and len(od["items"]) == 2 \
                        and _paid(world, oid):
                    return True
            return False
        if fam == "modify":
            for bid, bk in world.bookings.items():
                if bk["status"] != "confirmed" or not _paid(world, bid):
                    continue
                if bid not in world.modified:
                    continue
                fl = world.flights[bk["flight_id"]]
                if (fl["origin"], fl["dest"], fl["date"]) == \
                        (task["origin"], task["dest"], task["date"]):
                    return True
            return False
        return False

    return goal
