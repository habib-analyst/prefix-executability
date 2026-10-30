"""Tool schemas, validation, and execution.

Each tool declares: required args with types, and a precondition checked
against live state. ``validate`` classifies failures as one of:
  ok | unknown_tool | schema (missing arg / wrong type) |
  unknown_ref (a referenced id does not exist) | precondition.
``execute`` applies a validated call and returns (ok, output, error_kind).
Invalid calls are no-ops: the scorer records the first error and the
full rollout keeps replaying so final success / recovery stay defined
(paper §2.1: prefix replay fixes FED; the full rollout is retained).
"""

from __future__ import annotations

# tool -> {arg: type}
SCHEMAS = {
    "search_flights": {"origin": str, "dest": str, "date": str},
    "get_flight": {"flight_id": str},
    "create_booking": {"flight_id": str, "passenger": str},
    "confirm_booking": {"booking_id": str},
    "cancel_booking": {"booking_id": str},
    "modify_booking": {"booking_id": str, "new_flight_id": str},
    "pay_booking": {"booking_id": str, "amount": int},
    "search_products": {"query": str},
    "get_product": {"product_id": str},
    "create_order": {"product_id": str, "qty": int},
    "add_item": {"order_id": str, "product_id": str, "qty": int},
    "pay_order": {"order_id": str, "amount": int},
    "ship_order": {"order_id": str},
    "send_notification": {"ref_id": str, "channel": str},
}

# arg name -> entity kind, for unknown-reference classification + repair
REF_KIND = {
    "flight_id": "flight", "new_flight_id": "flight",
    "booking_id": "booking", "order_id": "order",
    "product_id": "product", "ref_id": "booking_or_order",
}


def _exists(world, kind, rid):
    if kind == "flight":
        return rid in world.flights
    if kind == "booking":
        return rid in world.bookings
    if kind == "order":
        return rid in world.orders
    if kind == "product":
        return rid in world.products
    if kind == "booking_or_order":
        return rid in world.bookings or rid in world.orders
    return False


def validate(world, tool, args):
    """Return (ok: bool, error_kind: str|None). Pure check, no mutation."""
    if tool not in SCHEMAS:
        return False, "unknown_tool"
    spec = SCHEMAS[tool]
    for name, typ in spec.items():
        if name not in args:
            return False, "schema"
        if not isinstance(args[name], typ) or isinstance(args[name], bool):
            return False, "schema"
    for name, kind in REF_KIND.items():
        if name in args and not _exists(world, kind, args[name]):
            return False, "unknown_ref"
    # Preconditions (state-dependent).
    if tool == "create_booking":
        if world.flights[args["flight_id"]]["seats"] <= 0:
            return False, "precondition"
    elif tool == "confirm_booking":
        if world.bookings[args["booking_id"]]["status"] != "held":
            return False, "precondition"
    elif tool == "cancel_booking":
        if world.bookings[args["booking_id"]]["status"] == "cancelled":
            return False, "precondition"
    elif tool == "modify_booking":
        bk = world.bookings[args["booking_id"]]
        nf = world.flights[args["new_flight_id"]]
        if bk["status"] != "confirmed" or nf["seats"] <= 0:
            return False, "precondition"
        if args["new_flight_id"] == bk["flight_id"]:
            return False, "precondition"
    elif tool == "pay_booking":
        bk = world.bookings[args["booking_id"]]
        fare = world.flights[bk["flight_id"]]["fare"]
        if bk["status"] != "confirmed" or args["amount"] != fare:
            return False, "precondition"
    elif tool == "create_order":
        if world.products[args["product_id"]]["stock"] < args["qty"]:
            return False, "precondition"
    elif tool == "add_item":
        od = world.orders[args["order_id"]]
        pr = world.products[args["product_id"]]
        if od["status"] != "created" or pr["stock"] < args["qty"]:
            return False, "precondition"
        if od["warehouse"] != pr["warehouse"]:
            return False, "precondition"
    elif tool == "pay_order":
        od = world.orders[args["order_id"]]
        if od["status"] != "created" or args["amount"] != od["total"]:
            return False, "precondition"
    elif tool == "ship_order":
        if world.orders[args["order_id"]]["status"] != "paid":
            return False, "precondition"
    elif tool == "send_notification":
        rid = args["ref_id"]
        if args["channel"] not in ("email", "sms"):
            return False, "schema"
        ok = False
        if rid in world.bookings and world.bookings[rid]["status"] == "confirmed":
            ok = True
        if rid in world.orders and world.orders[rid]["status"] in ("paid", "shipped"):
            ok = True
        if not ok:
            return False, "precondition"
    return True, None


def execute(world, tool, args):
    """Validate then apply. Returns (ok, output_dict, error_kind)."""
    ok, err = validate(world, tool, args)
    if not ok:
        return False, {}, err
    if tool == "search_flights":
        out = [fid for fid, f in world.flights.items()
               if f["origin"] == args["origin"] and f["dest"] == args["dest"]
               and f["date"] == args["date"]]
        return True, {"flight_ids": out}, None
    if tool == "get_flight":
        return True, {"flight": world.flights[args["flight_id"]]}, None
    if tool == "create_booking":
        bid = f"BK-{world.next_booking:03d}"
        world.next_booking += 1
        world.flights[args["flight_id"]]["seats"] -= 1
        world.bookings[bid] = {"flight_id": args["flight_id"],
                               "passenger": args["passenger"], "status": "held"}
        return True, {"booking_id": bid}, None
    if tool == "confirm_booking":
        world.bookings[args["booking_id"]]["status"] = "confirmed"
        return True, {}, None
    if tool == "cancel_booking":
        bk = world.bookings[args["booking_id"]]
        world.flights[bk["flight_id"]]["seats"] += 1
        bk["status"] = "cancelled"
        return True, {}, None
    if tool == "modify_booking":
        bk = world.bookings[args["booking_id"]]
        world.flights[bk["flight_id"]]["seats"] += 1
        world.flights[args["new_flight_id"]]["seats"] -= 1
        bk["flight_id"] = args["new_flight_id"]
        world.modified.add(args["booking_id"])
        return True, {}, None
    if tool == "pay_booking":
        pid = f"PY-{world.next_payment:03d}"
        world.next_payment += 1
        world.payments[pid] = {"ref_id": args["booking_id"], "amount": args["amount"]}
        return True, {"payment_id": pid}, None
    if tool == "search_products":
        out = [pid for pid, p in world.products.items()
               if p["category"] == args["query"]]
        return True, {"product_ids": out}, None
    if tool == "get_product":
        return True, {"product": world.products[args["product_id"]]}, None
    if tool == "create_order":
        oid = f"OR-{world.next_order:03d}"
        world.next_order += 1
        pr = world.products[args["product_id"]]
        pr["stock"] -= args["qty"]
        world.orders[oid] = {"items": [(args["product_id"], args["qty"])],
                             "status": "created",
                             "total": pr["price"] * args["qty"],
                             "warehouse": pr["warehouse"]}
        return True, {"order_id": oid}, None
    if tool == "add_item":
        od = world.orders[args["order_id"]]
        pr = world.products[args["product_id"]]
        pr["stock"] -= args["qty"]
        od["items"].append((args["product_id"], args["qty"]))
        od["total"] += pr["price"] * args["qty"]
        return True, {}, None
    if tool == "pay_order":
        pid = f"PY-{world.next_payment:03d}"
        world.next_payment += 1
        world.payments[pid] = {"ref_id": args["order_id"], "amount": args["amount"]}
        world.orders[args["order_id"]]["status"] = "paid"
        return True, {"payment_id": pid}, None
    if tool == "ship_order":
        world.orders[args["order_id"]]["status"] = "shipped"
        return True, {}, None
    if tool == "send_notification":
        return True, {}, None
    return False, {}, "unknown_tool"
