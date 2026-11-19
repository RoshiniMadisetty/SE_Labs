"""Campus Parking Permit Manager.

Issues permits for vehicles in zones A to C, revokes them, checks for
expired permits and flags vehicles that should not be parked in a zone.
"""
import json
import secrets
from datetime import datetime, timedelta

DATE_FORMAT = "%Y-%m-%d"
ZONES = ["A", "B", "C"]

# Shared permit store: plate -> {"zone", "permit", "expiry"}
permits = {}


def register_permit(vehicle_plate, zone_id, zone_records=None):
    """Issue a permit and return its number, or None if input is invalid."""
    if zone_records is None:
        zone_records = []
    if not isinstance(vehicle_plate, str) or not vehicle_plate.strip():
        return None
    if zone_id not in ZONES:
        return None
    permit_no = "P" + str(10000 + secrets.randbelow(90000))
    expiry = datetime.now() + timedelta(days=180)
    permits[vehicle_plate] = {
        "zone": zone_id,
        "permit": permit_no,
        "expiry": expiry.strftime(DATE_FORMAT),
    }
    zone_records.append((vehicle_plate, zone_id))
    return permit_no


def revoke_permit(vehicle_plate):
    """Remove a permit. Return True if one existed, otherwise False."""
    return permits.pop(vehicle_plate, None) is not None


def is_expired(vehicle_plate):
    """Return True if the permit is past its expiry date.

    A permit with a missing or unreadable expiry date counts as expired.
    A plate with no permit at all is not "expired" (it is simply unpermitted).
    """
    if vehicle_plate not in permits:
        return False
    try:
        expiry = datetime.strptime(
            permits[vehicle_plate]["expiry"], DATE_FORMAT
        )
    except (KeyError, ValueError, TypeError):
        return True
    return expiry < datetime.now()


def scan_zone(zone_id, plates_seen):
    """Return the plates that should not be parked in the given zone."""
    flagged = []
    for plate in plates_seen:
        permit = permits.get(plate)
        if (permit is None or permit["zone"] != zone_id
                or is_expired(plate)):
            flagged.append(plate)
    return flagged


def load_permit_database(file="permits.json"):
    """Load permits from a JSON file; start empty if it cannot be read."""
    try:
        with open(file, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        data = {}
    permits.clear()
    permits.update(data)


def save_permit_database(file="permits.json"):
    """Write all permits to a JSON file."""
    with open(file, "w", encoding="utf-8") as handle:
        json.dump(permits, handle)


def set_expiry(vehicle_plate, date_text):
    """Set a permit's expiry (YYYY-MM-DD). Return True on success."""
    if vehicle_plate not in permits:
        return False
    try:
        datetime.strptime(date_text, DATE_FORMAT)
    except (ValueError, TypeError):
        return False
    permits[vehicle_plate]["expiry"] = date_text
    return True


def main():
    """Run the permit manager demo."""
    load_permit_database()
    register_permit("KA01AB1234", "A")
    register_permit("KA05XY9999", "Z")   # rejected: unknown zone
    register_permit("", "B")             # rejected: empty plate
    register_permit(None, "C")           # rejected: no plate
    set_expiry("KA01AB1234", "2020-01-01")
    revoke_permit("MH12ZZ0000")
    flagged = scan_zone("A", ["KA01AB1234", "KA05XY9999", "TN09QQ1111"])
    print("Flagged in zone A:", flagged)
    plate = input("Plate to revoke (Enter to skip): ")
    if plate and not revoke_permit(plate):
        print("No permit found for", plate)
    save_permit_database()
    print("Permits on file:", len(permits))


if __name__ == "__main__":
    main()
