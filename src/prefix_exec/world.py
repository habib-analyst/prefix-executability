"""Synthetic airline/retail tool world for prefix-executability experiments.

A tiny deterministic world mirroring the tau^3-bench Airline/Retail shape:
flights with seats/fares, bookings with held/confirmed/cancelled states,
products with stock/warehouse, orders with created/paid/shipped states.
No network, no LLM, no GPU. Pure stdlib.
"""

from __future__ import annotations

import copy
import random

AIRLINES = ["AA", "BB", "CC"]
ROUTES = [("JFK", "LAX"), ("LAX", "JFK"), ("ORD", "DFW"), ("DFW", "ORD"), ("BOS", "MIA"), ("MIA", "BOS")]
DATES = ["2026-12-01", "2026-12-02"]
WAREHOUSES = ["W1", "W2", "W3"]
CATEGORIES = ["gadget", "widget", "tool"]
PASSENGER = "PAX1"


class World:
    """Mutable world state. ``fork()`` gives an isolated copy per replay."""

    def __init__(self, rng: random.Random):
        self.flights = {}   # id -> dict(origin, dest, date, airline, seats, fare)
        self.bookings = {}  # id -> dict(flight_id, passenger, status)
        self.products = {}  # id -> dict(category, warehouse, price, stock)
        self.orders = {}    # id -> dict(items=[(pid, qty)], status, total, warehouse)
        self.payments = {}  # id -> dict(ref_id, amount)
        self.modified = set()  # booking ids that went through modify_booking
        self.next_booking = 1
        self.next_order = 1
        self.next_payment = 1
        fid = 1
        for (o, d) in ROUTES:
            for date in DATES:
                # Shuffle airline order per route/date so flight-id order
                # does NOT systematically align airlines across routes:
                # a first-choice (myopic) policy must then match airlines
                # by luck (~1/3), while a coordinated plan can always
                # find a same-airline pair (one flight per airline).
                als = list(AIRLINES)
                rng.shuffle(als)
                for al in als:
                    self.flights[f"FL-{fid:03d}"] = {
                        "origin": o, "dest": d, "date": date, "airline": al,
                        "seats": rng.randint(1, 6), "fare": 100 + 10 * (fid % 9),
                    }
                    fid += 1
        # Decouple category from warehouse: the first 9 products cover all
        # (category, warehouse) combinations, so a same-warehouse second
        # bundle item always exists; a first-choice policy still matches
        # warehouses only by luck (~1/3).
        combos = [(c, w) for c in CATEGORIES for w in WAREHOUSES]
        rng.shuffle(combos)  # id order must not sort warehouses within a
        # category, or a first-choice policy matches warehouses by luck
        # of id order rather than by coordination (pilot v2 artifact).
        for i in range(12):
            if i < len(combos):
                cat, wh = combos[i]
            else:
                cat = CATEGORIES[rng.randrange(3)]
                wh = WAREHOUSES[rng.randrange(3)]
            self.products[f"PR-{i + 1:03d}"] = {
                "category": cat, "warehouse": wh,
                "price": 20 + 5 * i, "stock": rng.randint(1, 10),
            }

    def fork(self):
        return copy.deepcopy(self)


def new_world(seed: int) -> World:
    return World(random.Random(seed))
