from bson import ObjectId
from pymongo import MongoClient
from google import genai
from google.genai import types
from flask import Flask, render_template, request
import os
import certifi
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

#Para conectar la bd
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())

db = client["ERP-LLM"]


SYSTEM_INSTRUCTION = "Eres un gestor de un almacén tu salida debe ser una llamada a una función CRUD. No permitas borrar la base de datos entera"


def crear_recurso(nombreCol, datos):
    coleccion = db[nombreCol]

    #Habría que buscar el objeto primero y si existe solo actualizar el stock. En otro caso crearlo
    if(nombreCol=="productos" and coleccion.find_one({"nombre": datos["nombre"]})):
        res = coleccion.update_one({"nombre": datos["nombre"]}, {"$inc": {"stock": datos["stock"]}}) #inc para incrementar el valor del stock
        return "Stock actualizado"
    elif nombreCol== "productos":
        res = coleccion.insert_one(datos) 
        return "Recurso creado"
    elif coleccion.find_one({"nombre": datos["nombre"]}):
        res = coleccion.update_one({"nombre": datos["nombre"]}, {"$set": {"telefono": datos["telefono"]}})
        return "Telefono de proveedor actualizado"
    else :
        res = coleccion.insert_one(datos)
        return "Proveedor añadido"



def borrar_recurso(nombreCol,clave,cantidad):
    coleccion=db[nombreCol]

    recu = {"nombre": clave} #Hay que añadirle la función ObjectId porque mongodb no trabaja con textos en clave
    encon = coleccion.find_one({"nombre": clave})
    if encon is not None:
        stockrest = encon["stock"] - cantidad

        if(stockrest <= 0 ):
            res = coleccion.delete_one(recu)
            return "El producto se agotó y se eliminó del almacén"
        else:
            res= coleccion.update_one({"nombre":clave},{"$inc": {"stock": -cantidad }})
            return "Stock actualizado"
    else:
        return "No existe ese recurso en el almacén"


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
    "description": "Crea o actualiza un recurso en la base de datos (productos o proveedores) deduciendo el destino según el contexto.",
    "parameters": {
        "type": "object",
        "properties": {
            "nombreCol": {
                "type": "string",
                "description": "La colección de destino. Usa 'productos' si habla de mercancía, stock o comida. Usa 'proveedores' si habla de empresas, marcas o vendedores."
            },
            "datos": {
                "type": "object",
                "description": "Contiene los datos del elemento. Si es un producto, rellena: nombre, stock, precio, proveedor, categoria, fecha. Si es un proveedor, rellena: nombre, telefono (y opcionalmente email o direccion si el usuario los da).",
                "properties": {
                    "nombre": {"type": "string"},
                    "stock": {"type": "integer"},
                    "precio": {"type": "number"},
                    "proveedor": {"type": "string"},
                    "categoria": {"type": "string"},
                    "fecha": {"type": "string"},
                    "telefono": {"type": "string"},
                    "email": {"type": "string"},
                    "direccion": {"type": "string"}
                },
                # He metido todos los atributos para que no haya ambiguedad porque daba error. Pero solo exigimos el nombre
                "required": ["nombre"] 
            }
        },
        "required": ["nombreCol", "datos"]
    }
}

borrar_gemini = {
    "name": "borrar_gemini",
    "description": "Borra el stock de un recurso en la base de datos haciendo uso del nombre que se pase como parametro",
    "parameters": {
        "type": "object",
        "properties": {
            "nombreCol": {"type": "string"},
            "clave": {"type": "string" },
            "cantidad": {"type": "number"},
        },
        "required": ["nombreCol","clave","cantidad"]
    }
}



@app.route('/')
def inicio():
    #Flask ejecuta esto de primeras por eso queremos que se muestre el html aqui
    return render_template('index.html')

@app.route('/orden', methods=['POST'])
def procesar_orden():
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
        model="gemini-2.5-flash",
        contents=contents,
        config=config,
    )


    tool_call = response.candidates[0].content.parts[0].function_call

    mensajefinal = ""
    if tool_call is not None: #Es decir, si ha decidido hacer uso de una función
        if tool_call.name == "crear_gemini":
            mensajefinal = crear_recurso(**tool_call.args)
            print(f"Se ejecutó la función: {mensajefinal}")
        elif tool_call.name == "borrar_gemini":
            mensajefinal = borrar_recurso(**tool_call.args)
            print(f"Se ejecutó la función: {mensajefinal}")

        return render_template('index.html',resultado=mensajefinal)
    else: #Si no ha hecho uso de una funcion responder normalmente
        mensajefinal = response.text
    
    return render_template('index.html',resultado=mensajefinal)


if __name__ == '__main__':
    #Para que el programa se quede ejecutando indefinidamente 
    app.run(debug=True)