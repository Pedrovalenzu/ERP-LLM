from pymongo import MongoClient

from google import genai
from google.genai import types

ca = certifi.where()

#Para conectar la bd
client = MongoClient("mongodb+srv://pedrovaleji_db_user:vBYAtXBNPk2NW0Ns@cluster0.y2pklux.mongodb.net/?appName=Cluster0",tlsCAFile=ca)

db = client["ERP-LLM"]


SYSTEM_INSTRUCTION = "Eres un gestor de un almacén tu salida debe ser una llamada a una función CRUD. No permitas borrar la base de datos entera"


def crear_recurso(nombreCol, datos):
    coleccion = db[nombrecoleccion]

    #Habría que buscar el objeto primero y si existe solo actualizar el stock. En otro caso crearlo
    res = coleccion.insert_one(datos)



def borrar_recurso(nombreCol,clave):
    coleccion=db[nombrecoleccion]

    recu = {"_id": ObjectId(clave)} #Hay que añadirle la función ObjectId porque mongodb no trabaja con textos en clave

    res = coleccion.delete_one(recu)


def actualizar_recurso(nombreCol,clave,datos):
    coleccion = db[nombrecoleccion]
    filtro = {"_id": ObjectId(clave)}

    res = coleccion.update_one(filtro,{"$set": datos}) #Se usa set para no borrar el resto de campos


def leer_recurso(nombreCol,clave):
    coleccion = db[nombrecoleccion]

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
                    "stock": {"type": "integer"},
                    "precio": {"type": "number"}, #Por algún motivo es mejor usar "number" en vez de double
                    "proveedor":{"type": "string"},
                    "categoria": {"type": "string"},
                },
                "required": ["stock","precio","proveedor","categoria"]
            },

        },
        
        "required": ["nombreCol","datos"],
    },
}


gclient = genai.Client()
tools = types.Tool(function_declarations=[crear_gemini])



contents = [
    types.Content(
        role="user", parts=[types.Part(text="Añade 50 coles")] #Si el texto se parece gemini va a ejecutar la funcion de crear. Si no va a responder como el modelo normal
    )
]

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=contents,
    config=config,
)


tool_call = response.candidates[0].content.parts[0].function_call

if tool_call.name == "crear_gemini":
    result = crear_recurso(**tool_call.args)
    print(f"Function execution result: {result}")