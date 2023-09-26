from flask import Flask
from flask import render_template, request, redirect, session, jsonify
import networkx as nx
import json
from flaskext.mysql import MySQL
from datetime import datetime
import hashlib

app = Flask(__name__)

app.secret_key = "digitalforge"

# AGREGAR UN CONTROL DE TIEMPO DE LA SESION, (SOLO SI ES REQUERIDO)

mysql = MySQL()

app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_PORT'] = 3306
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'reto_ssoftt'

mysql.init_app(app)

conexion = mysql.connect()
cursor = conexion.cursor()


# Consulta las ubicaciones y conexiones desde la base de datos
cursor.execute('SELECT * FROM ubicaciones')
ubicaciones = cursor.fetchall()


cursor.execute('SELECT * FROM conexiones')
conexiones = cursor.fetchall()


# Crea un diccionario que contiene los datos
data = {
    "ubicaciones": [],
    "conexiones": [],
    "inicio": "A" # Establece el nodo de inicio según tus necesidades
}

# Procesa las ubicaciones y agrega al diccionario
for ubicacion in ubicaciones:
    nombre, posX, posY = ubicacion
    data["ubicaciones"].append({
        "nombre": nombre,
        "posX": posX,
        "posY": posY
    })

# Procesa las conexiones y agrega al diccionario
for conexion in conexiones:
    ubicacion1, ubicacion2, peso = conexion
    data["conexiones"].append({
        "ubicacion1": ubicacion1,
        "ubicacion2": ubicacion2,
        "peso": peso
    })


# Cierra la conexión a la base de datos


# Convierte los datos en formato JSON
json_data = json.dumps(data)

# Crea un gráfico vacío
G = nx.Graph()

# Agrega los nodos desde el JSON
for ubicacion in data["ubicaciones"]:
    nombre = ubicacion["nombre"]
    G.add_node(nombre, posX=ubicacion["posX"], posY=ubicacion["posY"])

# Agrega las aristas desde el JSON
for conexion in data["conexiones"]:
    ubicacion1 = conexion["ubicacion1"]
    ubicacion2 = conexion["ubicacion2"]
    peso = conexion["peso"]
    G.add_edge(ubicacion1, ubicacion2, weight=peso)



# Encuentra la ruta más corta entre los nodos especificados en el JSON
start_node = data["inicio"]
end_node = "D"  # Puedes cambiar esto según tus necesidades

print(G.nodes())

  # Puedes cambiar esto según tus necesidades

shortest_path = nx.shortest_path(G, start_node, end_node, weight='weight')
shortest_distance = nx.shortest_path_length(G, start_node, end_node, weight='weight')

print(f'Ruta más corta: {shortest_path}')
print(f'Distancia más corta: {shortest_distance}')



def pagina_no_encontrada(error):
    return render_template('errores/404.html'), 404

def inicializador_app():
    app.register_error_handler(404, pagina_no_encontrada)
    return app