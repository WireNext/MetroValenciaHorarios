import pandas as pd
from datetime import datetime

def servicios_activos_hoy(calendar_dates):
    hoy_str = datetime.today().strftime('%Y%m%d')
    activos = calendar_dates[
        (calendar_dates['date'] == int(hoy_str)) &
        (calendar_dates['exception_type'] == 1)
    ]
    return activos['service_id'].unique().tolist()

def proximos_horarios(stops, routes, trips, stop_times, calendar_dates):
    # Obtén los service_id activos hoy
    servicios_hoy = servicios_activos_hoy(calendar_dates)
    
    # Filtra viajes activos
    viajes_activos = trips[trips['service_id'].isin(servicios_hoy)]
    
    # Filtra stop_times para esos viajes
    stop_times_activos = stop_times[stop_times['trip_id'].isin(viajes_activos['trip_id'])]
    
    # Unir datos para mostrar info clara
    df = stop_times_activos.merge(stops, on='stop_id')
    df = df.merge(viajes_activos[['trip_id', 'route_id']], on='trip_id')
    df = df.merge(routes[['route_id', 'route_short_name']], on='route_id')
    
    # Convertir arrival_time a segundos para poder comparar con el tiempo actual
    def time_to_seconds(t):
        h,m,s = map(int, t.split(':'))
        return h*3600 + m*60 + s

    ahora = datetime.now()
    ahora_segundos = ahora.hour*3600 + ahora.minute*60 + ahora.second
    
    # Filtra horarios que vienen después de ahora
    df['arrival_seconds'] = df['arrival_time'].apply(time_to_seconds)
    proximos = df[df['arrival_seconds'] >= ahora_segundos]
    
    # Ordenar por línea, estación y hora
    proximos = proximos.sort_values(['route_short_name', 'stop_name', 'arrival_seconds'])
    
    # Mostrar próximo horario por línea y estación (el primero que viene)
    resultado = proximos.groupby(['route_short_name', 'stop_name']).first().reset_index()
    
    # Seleccionamos columnas relevantes para mostrar
    resultado = resultado[['route_short_name', 'stop_name', 'arrival_time']]
    
    return resultado

def main():
    # Cambia la ruta a donde tengas descomprimido el GTFS
    carpeta_gtfs = './gtfs_metrovalencia/'

    stops = pd.read_csv(carpeta_gtfs + 'stops.txt')
    routes = pd.read_csv(carpeta_gtfs + 'routes.txt')
    trips = pd.read_csv(carpeta_gtfs + 'trips.txt')
    stop_times = pd.read_csv(carpeta_gtfs + 'stop_times.txt')
    calendar_dates = pd.read_csv(carpeta_gtfs + 'calendar_dates.txt')

    horarios = proximos_horarios(stops, routes, trips, stop_times, calendar_dates)
    
    print(horarios)

if __name__ == "__main__":
    main()
