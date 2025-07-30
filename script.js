async function cargarDatosGTFS() {
  try {
    const baseURL = 'gtfs/';
    const [routes, trips, stops, stopTimes, calendarDates, shapes] = await Promise.all([
      fetch(baseURL + 'routes.json').then(r => r.json()),
      fetch(baseURL + 'trips.json').then(r => r.json()),
      fetch(baseURL + 'stops.json').then(r => r.json()),
      fetch(baseURL + 'stop_times.json').then(r => r.json()),
      fetch(baseURL + 'calendar_dates.json').then(r => r.json()),
      fetch(baseURL + 'shapes.json').then(r => r.json())
    ]);

    console.log("✅ Datos cargados");
    iniciarMapa(stops, stopTimes, trips, routes, shapes);

  } catch (e) {
    console.error("❌ Error cargando GTFS:", e);
    alert("Error cargando datos. Mira la consola.");
  }
}

function iniciarMapa(stops, stopTimes, trips, routes, shapes) {
  const map = L.map('map').setView([39.4699, -0.3763], 14); // Valencia

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  const busDivIcon = L.divIcon({
    html: `<div style="
      background: #0078A8; 
      border-radius: 50%; 
      width: 30px; 
      height: 30px; 
      display: flex; 
      justify-content: center; 
      align-items: center; 
      color: white; 
      font-weight: bold;
      font-size: 18px;
      ">
      🚇
      </div>`,
    className: '',
    iconSize: [30, 30],
    iconAnchor: [15, 30],
    popupAnchor: [0, -30]
  });

  // Estilo de parpadeo
  const style = document.createElement('style');
  style.innerHTML = `
    @keyframes parpadeo {
      0%, 100% { opacity: 1; }
      50% { opacity: 0; }
    }
    .parpadeo {
      animation: parpadeo 1s infinite;
      font-weight: bold;
      color: red;
    }
  `;
  document.head.appendChild(style);

  const clusterGroup = L.markerClusterGroup();

  stops.forEach(stop => {
    const marker = L.marker([stop.stop_lat, stop.stop_lon], { icon: busDivIcon });
    marker.bindPopup("Cargando...");

    marker.on('click', () => {
      const horarios = stopTimes
        .filter(st => st.stop_id === stop.stop_id)
        .map(st => {
          const trip = trips.find(t => t.trip_id === st.trip_id);
          if (!trip) return null;

          const ruta = routes.find(r => r.route_id === trip.route_id);
          if (!ruta) return null;

          return {
            linea: ruta.route_short_name || '',
            nombre: ruta.route_long_name || '',
            hora: st.departure_time
          };
        })
        .filter(h => h !== null)
        .sort((a, b) => a.hora.localeCompare(b.hora));

      const ahora = new Date();

      function horaAFecha(horaStr) {
        const [hh, mm, ss] = horaStr.split(':').map(Number);
        const fecha = new Date(ahora);
        fecha.setHours(hh, mm, ss, 0);
        return fecha;
      }

      const horariosConDiff = horarios.map(h => {
        const fechaSalida = horaAFecha(h.hora);
        let diffMin = (fechaSalida - ahora) / 60000;
        if (diffMin < 0) diffMin += 24 * 60;
        return { ...h, diffMin, fechaSalida };
      });

      horariosConDiff.sort((a, b) => a.diffMin - b.diffMin);
      const futuros = horariosConDiff.filter(h => h.diffMin >= 0);

      if (futuros.length === 0) {
        marker.setPopupContent(`<strong>${stop.stop_name}</strong><br>No hay más servicios hoy.`);
        return;
      }

      const proximosMinutos = futuros.slice(0, 2);
      const siguientesHoras = futuros.slice(2, 5);

      let html = `<strong>${stop.stop_name}</strong><br><ul>`;

      proximosMinutos.forEach(h => {
        if (h.diffMin <= 1) {
          html += `<li><b>${h.linea}</b> ${h.nombre}: <span class="parpadeo">en ${Math.round(h.diffMin)} min</span></li>`;
        } else {
          html += `<li><b>${h.linea}</b> ${h.nombre}: en ${Math.round(h.diffMin)} min</li>`;
        }
      });

      siguientesHoras.forEach(h => {
        html += `<li><b>${h.linea}</b> ${h.nombre}: ${h.hora}</li>`;
      });

      html += '</ul>';
      marker.setPopupContent(html);
    });

    clusterGroup.addLayer(marker);
  });

  map.addLayer(clusterGroup);

  // Dibujar shapes con route_color
  for (const shapeId in shapes) {
    const puntos = shapes[shapeId];

    puntos.sort((a, b) => parseInt(a.shape_pt_sequence) - parseInt(b.shape_pt_sequence));

    const latlngs = puntos.map(pt => [
      parseFloat(pt.shape_pt_lat),
      parseFloat(pt.shape_pt_lon)
    ]);

    // Buscar trip y ruta correspondiente
    const trip = trips.find(t => t.shape_id === shapeId);
    let color = '#0078A8'; // color por defecto

    if (trip) {
      const ruta = routes.find(r => r.route_id === trip.route_id);
      if (ruta && ruta.route_color) {
        color = '#' + ruta.route_color;
      }
    }

    L.polyline(latlngs, {
      color,
      weight: 3,
      opacity: 0.7
    }).addTo(map);
  }
}

cargarDatosGTFS();
