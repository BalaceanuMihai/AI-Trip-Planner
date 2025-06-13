import pandas as pd

columns = [
    "Airport ID", "Name", "City", "Country", "IATA", "ICAO",
    "Latitude", "Longitude", "Altitude", "Timezone", "DST",
    "Tz database time zone", "Type", "Source"
]

# Înlocuiește cu calea locală unde ai salvat fișierul
df = pd.read_csv("core/planner/data/airports.dat", header=None, names=columns)

# Păstrează doar coloanele relevante și filtrează codurile valide
df_filtered = df[["Name", "City", "Country", "IATA"]]
df_filtered = df_filtered[df_filtered["IATA"].apply(lambda x: isinstance(x, str) and x != "\\N")]

# Salvează CSV-ul final
df_filtered.to_csv("core/planner/data/airports_cleaned.csv", index=False)
print("✅ Exportat cu succes în airports_cleaned.csv")
