import requests
import zipfile
import io
import os
import pandas as pd
from datetime import datetime

def descargar_y_extraer_gtfs(url, carpeta_destino):
    os.makedirs(carpeta_destino, exist_ok=True)
    print("Descargando GTFS...")
    r = requests.get(url)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(carpeta_destino)
    print("GTFS descargado y descomprimido en", carpeta_destino)

def proximos_horarios(stops, routes, trips, stop_times, calendar_dates):
    hoy = datetime.today().strftime("%Y%m%d")
    # Filtrar servicios activos hoy por calendar_dates con exception_type=1 (servicio activo ese día)
    servicios_hoy = calendar_dates[(calendar_dates['date'] == int(hoy)) & (calendar_dates['exception_type'] == 1)]['service_id'].unique()
    
    trips_activos = trips[trips['service_id'].isin(servicios_hoy)]

    # Para cada parada, obtener los próximos metros que pasen hoy
    horarios = []

    for stop_id in stops['stop_id'].unique():
        # Filtrar paradas en stop_times para esta parada y trips activos
        tiempos = stop_times[(stop_times['stop_id'] == stop_id) & (stop_times['trip_id'].isin(trips_activos['trip_id']))]

        if tiempos.empty:
            continue
        
        # Ordenar por hora de llegada y filtrar solo próximos horarios respecto a la hora actual
        ahora = datetime.now().strftime("%H:%M:%S")
        tiempos = tiempos.sort_values(by='arrival_time')
        tiempos_proximos = tiempos[tiempos['arrival_time'] >= ahora]

        if tiempos_proximos.empty:
            continue

        proximo = tiempos_proximos.iloc[0]

        # Obtener info de línea
        trip = trips[trips['trip_id'] == proximo['trip_id']].iloc[0]
        route = routes[routes['route_id'] == trip['route_id']].iloc[0]

        horarios.append({
            'stop_id': stop_id,
            'stop_name': stops[stops['stop_id'] == stop_id]['stop_name'].values[0],
            'route_id': route['route_id'],
            'route_short_name': route.get('route_short_name', ''),
            'route_long_name': route.get('route_long_name', ''),
            'next_arrival': proximo['arrival_time']
        })

    return horarios

def main():
    url_gtfs = "http://www.metrovalencia.es/google_transit_feed/google_transit.zip"
    carpeta_gtfs = "./gtfs_metrovalencia/"

    descargar_y_extraer_gtfs(url_gtfs, carpeta_gtfs)

    stops = pd.read_csv(carpeta_gtfs + 'stops.txt')
    routes = pd.read_csv(carpeta_gtfs + 'routes.txt')
    trips = pd.read_csv(carpeta_gtfs + 'trips.txt')
    stop_times = pd.read_csv(carpeta_gtfs + 'stop_times.txt')
    calendar_dates = pd.read_csv(carpeta_gtfs + 'calendar_dates.txt')

    horarios = proximos_horarios(stops, routes, trips, stop_times, calendar_dates)

    # Mostrar resultados
    for h in horarios:
        print(f"Línea {h['route_short_name']} en parada {h['stop_name']} pasa a las {h['next_arrival']}")

if __name__ == "__main__":
    main()
