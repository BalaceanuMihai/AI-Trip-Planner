from hotels import get_hotels

hotels = get_hotels("bucuresti", "2025-07-23", "2025-07-27")
for h in hotels:
    print(h)
