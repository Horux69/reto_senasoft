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
app.config['MYSQL_DATABASE_DB'] = 'reto_ssoft'

mysql.init_app(app)

conexion = mysql.connect()
cursor = conexion.cursor()

@app.route('/')
def index():
    return render_template('sitio/index.html')

@app.route('/login')
def login():
    return render_template('auth/login.html')

@app.route('/registro')
def registro():
    return render_template('auth/registro.html')

@app.route('/formAdd')
def formAdd():
    return render_template('sitio/agregarUbi.html')

@app.route('/addUbicacion', methods=['POST'])
def addUbicacion():
    nombre = request.form['nombreUbi']
    posX = request.form['latitud']
    posY = request.form['longitud']

    conexion = mysql.connect()
    cursor = conexion.cursor()

    sql = f"INSERT INTO ubicaciones (nombre, posX, posY) VALUES ('{nombre}', '{posX}', '{posY}')"
    cursor.execute(sql)
    conexion.commit()
    conexion.close()
    return redirect('/formAdd')


@app.route('/data')
def get_data():
    cursor.execute("SELECT * FROM ubicaciones")
    ubicaciones = cursor.fetchall()

    cursor.execute("SELECT * FROM conexiones")
    conexiones = cursor.fetchall()

    data = []
    for ubicacion in ubicaciones:
        nombre, posX, posY = ubicacion
        data.append({
            "nombre": nombre,
            "posX": posX,
            "posY": posY
        })

    print("Ubicaciones:", ubicaciones)
    print("Conexiones:", conexiones)


    return jsonify({"ubicaciones": data, "conexiones": conexiones})

@app.route('/addJSON')
def addJSON():
    return render_template('sitio/cargarJson.html')

@app.route('/cargar_json', methods=['POST'])
def cargar_json():
    # Verificar si se envió un archivo JSON
    if 'json_file' not in request.files:
        return "No se seleccionó ningún archivo JSON."

    archivo = request.files['json_file']

    # Verificar si el archivo tiene un nombre y una extensión válidos
    if archivo.filename == '':
        return "El archivo no tiene un nombre válido."

    if archivo.filename.endswith('.json'):
        # Procesar el archivo JSON
        try:
            data = archivo.read()  # Leer el contenido del archivo
            datos_json = json.loads(data)  # Cargar el JSON en un diccionario

            # Inicializa la conexión a la base de datos
            conexion = mysql.connect()
            cursor = conexion.cursor()

            # Procesa las ubicaciones y guárdalas en la tabla 'ubicaciones'
            for ubicacion in datos_json['ubicaciones']:
                nombre = ubicacion['nombre']
                posX = ubicacion['posX']
                posY = ubicacion['posY']
                cursor.execute("INSERT INTO ubicaciones (nombre, posX, posY) VALUES (%s, %s, %s)", (nombre, posX, posY))
                conexion.commit()

            # Procesa las conexiones y guárdalas en la tabla 'conexiones'
            for conexionn in datos_json['conexiones']:
                ubicacion1 = conexionn['ubicacion1']
                ubicacion2 = conexionn['ubicacion2']
                peso = conexionn['peso']
                cursor.execute("INSERT INTO conexiones (ubicacion1, ubicacion2, peso) VALUES (%s, %s, %s)", (ubicacion1, ubicacion2, peso))
                conexion.commit()

            cursor.close()  # Cierra el cursor
            conexion.close()  # Cierra la conexión

            return "Archivo JSON cargado y procesado correctamente."
        except Exception as e:
            return f"Error al procesar el archivo JSON: {str(e)}"
    else:
        return "El archivo no tiene una extensión JSON válida."






# Consulta las ubicaciones y conexiones desde la base de datos
cursor.execute('SELECT * FROM ubicaciones')
ubicaciones = cursor.fetchall()


cursor.execute('SELECT * FROM conexiones')
conexiones = cursor.fetchall()


# Crea un diccionario que contiene los datos
data = {
    "ubicaciones": [],
    "conexiones": [],
    "inicio": "Barranquilla" # Establece el nodo de inicio
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
end_node = "Medellin"  # Puedes cambiar esto según tus necesidades

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