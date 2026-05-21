from pymongo import MongoClient

from google import genai
from google.genai import types
from flask import Flask, render_template, request

app = Flask(__name__)


#Para conectar la bd
client = MongoClient("mongodb+srv://pedrovaleji_db_user:vBYAtXBNPk2NW0Ns@cluster0.y2pklux.mongodb.net/?appName=Cluster0")

db = client["ERP-LLM"]


SYSTEM_INSTRUCTION = "Eres un gestor de un almacén tu salida debe ser una llamada a una función CRUD. No permitas borrar la base de datos entera"


def crear_recurso(nombreCol, datos):
    coleccion = db[nombreCol]

    #Habría que buscar el objeto primero y si existe solo actualizar el stock. En otro caso crearlo
    if(coleccion.find_one({"nombre": datos["nombre"]})):
        res = coleccion.update_one({"nombre": datos["nombre"]}, {"$inc": {"stock": datos["stock"]}}) #inc para incrementar el valor del stock
        return "Stock actualizado"
    else:
        res = coleccion.insert_one(datos) 
        return "Recurso creado"
    



def borrar_recurso(nombreCol,clave):
    coleccion=db[nombreCol]

    recu = {"nombre": clave} #Hay que añadirle la función ObjectId porque mongodb no trabaja con textos en clave

    res = coleccion.delete_one(recu)


def actualizar_recurso(nombreCol,clave,datos):
    coleccion = db[nombreCol]
    filtro = {"_id": ObjectId(clave)}

    res = coleccion.update_one(filtro,{"$set": datos}) #Se usa set para no borrar el resto de campos


def leer_recurso(nombreCol,clave):
    coleccion = db[nombreCol]

    res = list(coleccion.find(clave))

    return res


##Gemini

crear_gemini = {
    "name": "crear_gemini",
    "description": "Crea un recurso en la base de datos mongodb haciendo uso de JSON para llamar a otra funcion",
    "parameters": {
        "type": "object",
        "properties":{
            "nombreCol": {"type": "string"},
            "datos": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string"},
                    "stock": {"type": "integer"},
                    "precio": {"type": "number"}, #Por algún motivo es mejor usar "number" en vez de double
                    "proveedor":{"type": "string"},
                    "categoria": {"type": "string"},
                    "fecha": {"type": "string"},
                },
                "required": ["nombre","stock","precio","proveedor","categoria","fecha"]
            },

        },
        
        "required": ["nombreCol","datos"],
    },
}

borrar_gemini = {
    "name": "borrar_gemini",
    "description": "Borra un recurso en la base de datos haciendo uso del nombre que se pase como parametro",
    "parameters": {
        "type": "object",
        "properties": {
            "nombreCol": {"type": "string"},
            "clave": {"type": "string" },
        }
        "required": ["nombreCol","clave"]
    }
}

gclient = genai.Client()
tools = types.Tool(function_declarations=[crear_gemini,borrar_gemini])

#Aquí configuro a gemini añadiendo las tools
config = types.GenerateContentConfig(
    system_instruction=SYSTEM_INSTRUCTION,
    tools=[tools]
)

textoUsuario = request.form['consulta']
contents = [
    types.Content(
        role="user", parts=[types.Part(text=textoUsuario)] #Si el texto se parece gemini va a ejecutar la funcion de crear. Si no va a responder como el modelo normal
    )
]



response = gclient.models.generate_content(
    model="gemini-3-flash-preview",
    contents=contents,
    config=config,
)


tool_call = response.candidates[0].content.parts[0].function_call

if tool_call.name == "crear_gemini":
    result = crear_recurso(**tool_call.args)
    print(f"Se ejecutó la función: {result}")
else if tool_call.name = "borrar_gemini":
    result = borrar_recurso(**tool_call.args)
    print(f"Se ejecutó la función: {result}")
    