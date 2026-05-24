from bson import ObjectId
from pymongo import MongoClient
from google import genai
from google.genai import types
from flask import Flask, render_template, request
import os
import certifi
from dotenv import load_dotenv
from datetime import datetime #Quiero meterle la fecha a la tabla pedidos 
load_dotenv()

app = Flask(__name__)

#Para conectar la bd
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())

db = client["ERP-LLM"]


SYSTEM_INSTRUCTION = "Eres un gestor de un almacén tu salida debe ser una llamada a una función CRUD. No permitas borrar la base de datos entera"


def crear_recurso(nombreCol, datos):
    coleccion = db[nombreCol]
    
    prod_exist = coleccion.find_one({"nombre": datos["nombre"]})
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #Habría que buscar el objeto primero y si existe solo actualizar el stock. En otro caso crearlo
    if(nombreCol=="productos" and prod_exist ):
        res = coleccion.update_one({"nombre": datos["nombre"]}, {"$inc": {"stock": datos["stock"]}}) #inc para incrementar el valor del stock
        
        #Para meter en la tabla de pedidos
        prov = prod_exist.get("proveedor", "Proveedor No Especificado")
        cant = datos.get("stock", 0)
        db["pedidos"].insert_one({"proveedor": prov, "stock": cant,"fecha": fecha})
        

        return "Stock actualizado"
    elif nombreCol== "productos":
        res = coleccion.insert_one(datos) 

        prov = datos.get("proveedor", "Proveedor No especificado")
        cant = datos.get("stock", 0)

        db["pedidos"].insert_one({"proveedor": proveedor, "stock": cant,"fecha": fecha})
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


def leer_recurso(nombreCol,clave):
    coleccion = db[nombreCol]

    res = list(coleccion.find(clave))

    return res


##Gemini

crear_gemini = {
    "name": "crear_gemini",
    "description": "Crea o actualiza un recurso en la base de datos (productos o proveedores) deduciendo el destino según el contexto. No seas case sensitive",
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
    "description": "Borra el stock de un recurso en la base de datos haciendo uso del nombre que se pase como parametro. Si el usuario Pide borrar todos borrarás todos. No seas case sensitive",
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

def obtenerDatosGraf(): #He tenido que crear esta función aparte porque al enviar una consulta Flask no se acordaba de los valores de los productos
    coleccion_prod = db["productos"]
    todos_los_productos = coleccion_prod.find({})
    
    nombres_prod = []
    stocks_prod = []
    
    for prod in todos_los_productos:
        nombres_prod.append(prod["nombre"])
        stocks_prod.append(prod["stock"])

    return nombres_prod, stocks_prod


def obtener_datos_proveedores():
    coleccion_pedidos = db["pedidos"]
    todos_los_pedidos = coleccion_pedidos.find({})
    
    # Diccionario para acumular: {"NombreProveedor": TotalProductos}
    conteo_proveedores = {}
    
    for pedido in todos_los_pedidos:
        prov = pedido.get("proveedor", "Desconocido")# Como antes, estoy usando get por si alguno no tiene proveedor para que no falle
        cant = pedido.get("stock", 0)
        
        # Esto es para ir acumulando la cantidad de productos pedidos a un proveedor
        if prov in conteo_proveedores:
            conteo_proveedores[prov] += cant  
        else:
            conteo_proveedores[prov] = cant   
            
    lista_proveedores = list(conteo_proveedores.keys())   
    lista_totales = list(conteo_proveedores.values())       
    
    return lista_proveedores, lista_totales



@app.route('/') #Flask ejecuta esto de primeras por eso queremos que se muestre el html aqui
def inicio():
    nombres, stocks = obtenerDatosGraf()
    proveedores, totales_prov = obtener_datos_proveedores()
    return render_template('index.html', labels_productos=nombres, datos_productos=stocks, labels_proveedores=proveedores, datos_proveedores=totales_prov)
                    
fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

        
    else: #Si no ha hecho uso de una funcion responder normalmente
        mensajefinal = response.text
    
    nombres, stock = obtenerDatosGraf()
    proveedores, totales_prov = obtener_datos_proveedores()
    return render_template('index.html',resultado=mensajefinal,labels_productos=nombres, datos_productos= stock, labels_proveedores=proveedores, datos_proveedores=totales_prov)



if __name__ == '__main__':
    #Para que el programa se quede ejecutando indefinidamente 
    app.run(debug=True)