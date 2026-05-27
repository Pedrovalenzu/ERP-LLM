from bson import ObjectId
from pymongo import MongoClient
from google import genai
from google.genai import types
from flask import Flask, render_template, request
import os
import certifi
from dotenv import load_dotenv
from datetime import datetime #Quiero meterle la fecha a la tabla pedidos
import ollama
import json
from groq import Groq  

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

        db["pedidos"].insert_one({"proveedor": prov, "stock": cant,"fecha": fecha})
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

    producto = coleccion.find_one({"nombre": clave})
    
    if producto:
        return f"El producto '{clave}' tiene actualmente {producto.get('stock', 0)} unidades en stock."
    else:
        return f"No se encontró ningún producto con el nombre '{clave}' en el almacén."



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

buscar_gemini = {
    "name": "buscar_gemini",
    "description": "Busca un recurso (producto o mercancía) en el almacén para consultar su stock actual. No seas case sensitive.",
    "parameters": {
        "type": "object",
        "properties": {
            "nombreCol": {
                "type": "string",
                "description": "La colección donde buscar. Usa siempre 'productos' para mercancía o comida."
            },
            "clave": {
                "type": "string",
                "description": "El nombre exacto del producto que el usuario quiere buscar (ej: 'patatas', 'manzanas')."
            }
        },
        "required": ["nombreCol", "clave"]
    }
}


def obtenerDatosGraf(): #He tenido que crear esta función aparte porque al enviar una consulta Flask no se acordaba de los valores de los productos
    coleccion_prod = db["productos"]
    todos_los_productos = coleccion_prod.find({})
    
    nombres_prod = []
    stocks_prod = []
    
    for prod in todos_los_productos:
        nombres_prod.append(prod.get("nombre", "Producto Sin Nombre"))
        stocks_prod.append(prod.get("stock", 0))

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


def consultar_ollama_local(texto_usuario): 
   
    prompt_estricto = (#Le he tenido que dar instrucciones mas concretas porque este modelo es mucho mas "tonto"
        f"{SYSTEM_INSTRUCTION}\n"
        "Debes analizar la solicitud del usuario y responder ÚNICAMENTE con un objeto JSON. "
        "No agregues texto explicativo, ni saludos, ni marcas de bloques de código (```json).\n\n"
        "Sigue estrictamente estos formatos según el caso:\n"
        "1. Si quiere añadir o crear stock:\n"
        '{"funcion": "crear", "nombreCol": "productos", "datos": {"nombre": "patatas", "stock": 10}}\n\n'
        "2. Si quiere retirar, descontar o borrar stock:\n"
        '{"funcion": "borrar", "nombreCol": "productos", "clave": "patatas", "cantidad": 10}\n\n'
        "3. Si quiere buscar o consultar stock:\n"
        '{"funcion": "buscar", "nombreCol": "productos", "clave": "patatas"}\n\n'
        "4. Si es una conversación o duda general:\n"
        '{"funcion": "texto", "contenido": "Aquí tu respuesta hablándole al usuario"}'
    )
    
    response = ollama.chat(
        model='llama3.1',
        messages=[
            {'role': 'system', 'content': prompt_estricto},
            {'role': 'user', 'content': texto_usuario}
        ],
        format='json'  #Si le añado esto va a tener que responderme con un JSON válido
    )
    # Devolvemos el texto plano de la respuesta
    return response['message']['content'].strip()

def consultar_groq_cloud(texto_usuario):#
    client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    #Le he tenido que cambiar el formato a la forma de llamar a las herramientas porque la API de grok sigue el formato de OpenAi en vez de el de gemini 
    herramientas_groq = [ 
        {"type": "function", "function": crear_gemini},
        {"type": "function", "function": borrar_gemini},
        {"type": "function", "function": buscar_gemini}
    ]

    response = client_groq.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": texto_usuario}
        ],
        tools=herramientas_groq
    )
    
    return response.choices[0].message


@app.route('/') #Flask ejecuta esto de primeras por eso queremos que se muestre el html aqui
def inicio():
    nombres, stocks = obtenerDatosGraf()
    proveedores, totales_prov = obtener_datos_proveedores()
    return render_template('index.html', labels_productos=nombres, datos_productos=stocks, labels_proveedores=proveedores, datos_proveedores=totales_prov)
                    
fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@app.route('/orden', methods=['POST'])
def procesar_orden():

    textoUsuario= request.form['consulta']
    modelo_selec = request.form.get('modelo_elegido', 'gemini')
    mensajefinal = ""

    #MODELO DE GEMINI
    if modelo_selec == "gemini":
        gclient = genai.Client()
        tools = types.Tool(function_declarations=[crear_gemini,borrar_gemini,buscar_gemini])

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

        
        if tool_call is not None: #Es decir, si ha decidido hacer uso de una función
            if tool_call.name == "crear_gemini":
                mensajefinal = crear_recurso(**tool_call.args)
                
            elif tool_call.name == "borrar_gemini":
                mensajefinal = borrar_recurso(**tool_call.args)
                
            elif tool_call.name == "buscar_gemini":
                mensajefinal = leer_recurso(**tool_call.args)

            print(f"Se ejecutó la función: {mensajefinal}")

            
        else: #Si no ha hecho uso de una funcion responder normalmente
            mensajefinal = response.text
        
    #Modelo Ollama
    elif modelo_selec == "ollama":
        respuesta_json_texto = consultar_ollama_local(textoUsuario)

        try:
            data = json.loads(respuesta_json_texto)
            nombre_funcion = data.get("funcion")
            nombre_columna = data.get("nombreCol", "productos")

            if nombre_funcion == "crear":
                mensajefinal = crear_recurso(nombre_columna, data.get("datos", {}))
            elif nombre_funcion == "borrar":
                mensajefinal = borrar_recurso(nombre_columna, data.get("clave"), int(data.get("cantidad", 0)))
            elif nombre_funcion == "buscar":
                mensajefinal = leer_recurso(nombre_columna, data.get("clave"))
            else:
                # Si es una respuesta conversacional
                mensajefinal = data.get("contenido", "Consulta procesada de forma genérica.")
                
        except Exception as e:
            mensajefinal = f"Error en el formato del modelo local. Respuesta original: {respuesta_json_texto}"

    #MODELO DE DEEPSEEK
    elif modelo_selec == "groq":
        mensaje_ia = consultar_groq_cloud(textoUsuario)
        print(f"DEBUG GROQ RESPONDIÓ: {mensaje_ia}")

        
        if mensaje_ia.tool_calls:
            funcion_solicitada = mensaje_ia.tool_calls[0].function
            nombre_funcion = funcion_solicitada.name
            
            argumentos = json.loads(funcion_solicitada.arguments)
            
            print(f"¡Groq ha ejecutado nativamente la función: {nombre_funcion}!")

            if nombre_funcion == "crear_gemini":
                mensajefinal = crear_recurso(argumentos.get('nombreCol'), argumentos.get('datos'))
            elif nombre_funcion == "borrar_gemini":
                mensajefinal = borrar_recurso(argumentos.get('nombreCol'), argumentos.get('clave'), argumentos.get('cantidad'))
            elif nombre_funcion == "buscar_gemini":
                mensajefinal = leer_recurso(argumentos.get('nombreCol'), argumentos.get('clave'))
        else:
            
            mensajefinal = mensaje_ia.content

    nombres, stock = obtenerDatosGraf()
    proveedores, totales_prov = obtener_datos_proveedores()
    return render_template('index.html',resultado=mensajefinal,labels_productos=nombres, datos_productos= stock, labels_proveedores=proveedores, datos_proveedores=totales_prov)
    

if __name__ == '__main__':
    #Para que el programa se quede ejecutando indefinidamente 
    app.run(debug=True)