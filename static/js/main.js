var map = L.map('map').setView([0, 0], 2);
    
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
}).addTo(map);

// Haz una solicitud para obtener los datos de ubicaciones y conexiones desde Flask
fetch('/data')
    .then(response => response.json())
    .then(data => {
        // Crear marcadores para ubicaciones
        var markers = [];
        data.ubicaciones.forEach(ubicacion => {
            var marker = L.marker([ubicacion.posX, ubicacion.posY]).addTo(map)
                .bindPopup(ubicacion.nombre);
            markers.push(marker);
        });
        
        // Crear líneas de conexión
        data.conexiones.forEach(connection => {
            var ubicacion1 = data.ubicaciones.find(item => item.nombre === connection.ubicacion1);
            var ubicacion2 = data.ubicaciones.find(item => item.nombre === connection.ubicacion2);
            
            console.log("Datos de ubicaciones:", data.ubicaciones);
            console.log("Datos de conexiones:", data.conexiones);


            if (ubicacion1 && ubicacion2) {
                var latLng1 = L.latLng(ubicacion1.posX, ubicacion1.posY);
                var latLng2 = L.latLng(ubicacion2.posX, ubicacion2.posY);
                L.polyline([latLng1, latLng2]).addTo(map);
            }
        });
    });
