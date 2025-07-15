# procesar_gtfs.py
import os
import requests
import zipfile
import io
import pandas as pd
from datetime import datetime

GTFS_URL = "http://www.metrovalencia.es/google_transit_feed/google_transit.zip"
OUTPUT = "horarios.json"

def descarga_y_lee_gtfs():
    r = requests.get(GTFS_URL)
    zb = zipfile.ZipFile(io.BytesIO(r.content))
    fs = {name: zb.open(name) for name in zb.namelist()}
    return (
        pd.read_csv(fs["stops.txt"]),
        pd.read_csv(fs["routes.txt"]),
        pd.read_csv(fs["trips.txt"]),
        pd.read_csv(fs["stop_times.txt"]),
        pd.read_csv(fs["calendar_dates.txt"]),
    )

def proximos_horarios(stops, routes, trips, stop_times, calendar):
    ahora = datetime.now().strftime("%H:%M:%S")
    today = calendar.apply(lambda row: datetime.today().weekday() in
                           [i for i,d in enumerate(row[["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]]) if d==1], axis=1)
    activos = calendar[today.index[today]]
    viajes_activos = trips[trips["service_id"].isin(activos["service_id"])]
    stops_sel = stops
    data = {}

    merged = stop_times.merge(viajes_activos, on="trip_id").merge(routes, on="route_id")
    merged = merged[merged["arrival_time"] >= ahora]

    for route_id, grupo in merged.groupby("route_id"):
        linea = grupo["route_short_name"].iloc[0]
        nombre = f"Línea {linea}"
        estaciones = []
        for stop_id, gr2 in grupo.groupby("stop_id"):
            hora = gr2["arrival_time"].min()
            parada_nombre = stops_sel[stops_sel["stop_id"] == stop_id]["stop_name"].iloc[0]
            estaciones.append({"nombre": parada_nombre, "hora": hora[:5]})
        estaciones.sort(key=lambda x: x["hora"])
        data[linea] = {"nombre": nombre, "paradas": estaciones}

    return data

if __name__ == "__main__":
    stops, routes, trips, stop_times, calendar = descarga_y_lee_gtfs()
    data = proximos_horarios(stops, routes, trips, stop_times, calendar)
    import json
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Generado {OUTPUT} con líneas: {', '.join(data.keys())}")
