from flask import Flask
from flask import render_template, request, redirect, session, jsonify, url_for
import networkx as nx
import json
from flaskext.mysql import MySQL
from datetime import datetime
import hashlib
from flask_jwt_extended import JWTManager, create_access_token
from email.message import EmailMessage
import ssl
import smtplib
import os

app = Flask(__name__)

app.secret_key = "digitalforge"

# AGREGAR UN CONTROL DE TIEMPO DE LA SESION, (SOLO SI ES REQUERIDO)

mysql = MySQL()

app.config['MYSQL_DATABASE_HOST'] = 'reto-senasoft.mysql.database.azure.com'
app.config['MYSQL_DATABASE_PORT'] = 3306
app.config['MYSQL_DATABASE_USER'] = 'camilo'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Reto1234'
app.config['MYSQL_DATABASE_DB'] = 'reto_ssoft'

mysql.init_app(app)

conexion = mysql.connect()
cursor = conexion.cursor()

@app.route('/index')
def index():
    return render_template('sitio/index.html')




@app.route('/')
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

# Calcular la ruta mas corta

@app.route('/rutaCorta', methods = ['POST'])
def rutaCorta():
    # Consulta las ubicaciones y conexiones desde la base de datos
    cursor.execute('SELECT * FROM ubicaciones')
    ubicaciones = cursor.fetchall()


    cursor.execute('SELECT * FROM conexiones')
    conexiones = cursor.fetchall()


    # Crea un diccionario que contiene los datos
    data = {
        "ubicaciones": [],
        "conexiones": [],
        "inicio": "" # Establece el nodo de inicio
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
    start_node = request.form['ubicacion1']
    end_node = request.form['ubicacion2']  # Puedes cambiar esto según tus necesidades



    print(G.nodes())

    # Puedes cambiar esto según tus necesidades

    shortest_path = nx.shortest_path(G, start_node, end_node, weight='weight')
    shortest_distance = nx.shortest_path_length(G, start_node, end_node, weight='weight')

    print(f'Ruta más corta: {shortest_path}')
    print(f'Distancia más corta: {shortest_distance}')

    return render_template('sitio/index.html', mensaje = shortest_path)




#Verificaion de cuenta por correo


# Configura la clave secreta para JWT (debe ser segura en un entorno real)
app.config['SECRET_KEY'] = os.urandom(24)

# Configura el JWT Manager
jwt = JWTManager(app)

# Ruta para registrar un nuevo usuario y luego enviar el correo de verificación
@app.route('/registro', methods=['POST'])
def register():
    try:
        # Procesa el formulario de registro y almacena los datos en la base de datos
        nombre = request.form['nombre']
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        cifrada = hashlib.sha512(contrasena.encode("utf-8")).hexdigest()

        # Crea un token de verificación usando JWT
        verification_token = create_access_token(identity=correo)
        print(verification_token)

        # Inserta los datos del usuario en tu base de datos
        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO usuarios (full_name, email, password, token, verified) VALUES (%s, %s, %s, %s, %s)", (nombre, correo, cifrada, verification_token, 0))
        conexion.commit()
        cursor.close()
        conexion.close()

        # Aquí se envía un correo electrónico de verificación con el token
        asunto = 'Verificación de correo'

        # Crea un mensaje de correo electrónico
        cuerpo = f'Por favor, haga clic en el siguiente enlace para verificar su correo: http://127.0.0.1:5000/verify_email/{verification_token}'

       
        email_emisor = 'cdvanegas830@misena.edu.co'  # Correo de prácticas
        email_contrasena = 'sagenav0'

        em = EmailMessage()
        em['From'] = email_emisor
        em['To'] = correo
        em['Subject'] = asunto
        em.set_content(cuerpo)

        # Configura el contexto SSL
        contexto = ssl.create_default_context()

        # Envía el correo electrónico
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=contexto) as smtp:
            smtp.login(email_emisor, email_contrasena)
            smtp.sendmail(email_emisor, correo, em.as_string())

        return "Registro exitoso. Se ha enviado un correo de verificación."

    except Exception as e:
        print(str(e))
        return "Error al registrar al usuario."


# Ruta para verificar el token y redirigir al usuario a la página principal
@app.route('/verify_email/<token>', methods=['GET'])
def verify_email(token):
    print(token)
    try:
        # Verifica si el token existe en la base de datos
        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("SELECT email FROM usuarios WHERE token = %s", (token,))
        correo = cursor.fetchone()
        cursor.close()
        print(correo)

        if correo:
            # Token válido, marca la cuenta de usuario como verificada en la base de datos
            cursor = conexion.cursor()
            cursor.execute("UPDATE usuarios SET verified = 1 WHERE email = %s", (correo[0],))
            conexion.commit()
            cursor.close()
            conexion.close()

            # Redirige al usuario a la página principal
            return redirect('/index')
        else:
            return "Token de verificación no válido."

    except Exception as e:
        print(str(e))
        return "Error al verificar el token."

# Ruta para la página principal
@app.route('/main_page', methods=['GET'])
def main_page():
    return "Bienvenido a la página principal."


#validacion de login

@app.route('/validationLogin', methods = ['POST'])
def ValidationLogin():
    if request.method == 'POST':
        correo = request.form['correo']
        contrasena = request.form['contrasena']

        encriptada = hashlib.sha512(contrasena.encode("utf-8")).hexdigest()

        conexion = mysql.connect()
        cursor = conexion.cursor()

        consulta = f"SELECT * FROM usuarios WHERE email = '{correo}' AND verified = 1"
        cursor.execute(consulta)
        resultado = cursor.fetchall()
        conexion.commit()


        print(resultado)

        if len(resultado) > 0:
            if encriptada == resultado[0][2]:
                session["logueado"] = True
                session["user_name"] = resultado[0][0]
                session["veficado"] = resultado[0][4]

                if session["logueado"] == True:
                    return render_template("sitio/index.html")
                else:
                    return render_template("auth/login.html", mensaje = "Acesso denegado")

            else:
                return render_template('auth/login.html', mensaje = "Acesso denegado")



def pagina_no_encontrada(error):
    return render_template('errores/404.html'), 404

def inicializador_app():
    app.register_error_handler(404, pagina_no_encontrada)
    return app