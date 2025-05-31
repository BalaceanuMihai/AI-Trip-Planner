from activities import get_activities

activities = get_activities("Riga")
for act in activities:
    print("🎯", act)
