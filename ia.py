from pymongo import MongoClient

ca = certifi.where()

#Para conectar la bd
client = MongoClient("mongodb+srv://pedrovaleji_db_user:vBYAtXBNPk2NW0Ns@cluster0.y2pklux.mongodb.net/?appName=Cluster0",tlsCAFile=ca)

db = client["ERP-LLM"]


SYSTEM_INSTRUCTION = "Eres un gestor de un almacén tu salida debe ser una llamada a una función CRUD. No permitas borrar la base de datos entera"


def crear_recurso(nombrecoleccion, datos):
    coleccion = db[nombrecoleccion]

    res = coleccion.insert_one(datos)


def borrar_recurso(nombrecoleccion,clave):
    coleccion=db[nombrecoleccion]

    recu = {"_id": clave}

    res = coleccion.delete_one(recu)


def actualizar_recurso(nombrecoleccion,clave,datos):
    coleccion = db[nombrecoleccion]
    filtro = {"_id": clave}

    res = coleccion.update_one(filtro,datos)

def leer_recurso(nombrecoleccion,clave):
    coleccion = db[nombrecoleccion]

    res = list(coleccion.find(clave))

    return res







