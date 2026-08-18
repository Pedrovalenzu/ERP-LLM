# ERP Conversacional para Gestión de Almacén (LLM Function Calling)

Prototipo experimental de un sistema de Planificación de Recursos Empresariales (ERP) enfocado en el control de existencias e inventario mediante interfaces de lenguaje natural (NLI) y llamadas a funciones (*Function Calling*) con Modelos de Lenguaje (LLM).

Desarrollado para la asignatura **Sistemas de Información Empresarial (SIE)** en la **Universidad de Málaga (UMA)**.

---

## Descripción del Proyecto

Las interfaces tradicionales de ERP exigen que el personal administrativo rellene formularios rígidos, busque códigos manualmente o gestione tablas extensas en hojas de cálculo. Este proyecto evalúa la viabilidad técnica, el rendimiento y la fiabilidad de sustituir los formularios convencionales por un **flujo conversacional automatizado mediante el uso de herramientas e IA generativa**.

El sistema interpreta las peticiones en lenguaje natural del usuario y ejecuta dinámicamente funciones del *backend* (operaciones CRUD) para gestionar entradas (compras), salidas (ventas/desechos) y consultas de stock en tiempo real.

---

## Características Principales

* **Control de Inventario Conversacional:** Gestión de altas, bajas y consultas de existencias mediante órdenes en lenguaje natural.
* **Llamada a Funciones (*Function Calling*):** Mapeo dinámico de intenciones a funciones Python que modifican o consultan la base de datos de forma directa.
* **Visualización de Datos en Tiempo Real:** Generación automática de gráficas para el seguimiento visual del estado del inventario.
* **Evaluación Multimodelo:** Comparación empírica entre modelos en la nube y modelos de pesos abiertos ejecutados en local.

---

## Comparativa y Evaluación de Modelos

Se implementó y analizó el comportamiento de distintos LLMs como orquestadores del sistema:

| Modelo | Entorno | Puntos Fuertes | Limitaciones Detectadas |
| :--- | :--- | :--- | :--- |
| **Google Gemini** | API Cloud | Alta precisión en *function calling*, tiempos de respuesta reducidos y consistencia en estructuras JSON. | Problemas puntuales al discriminar mayúsculas/minúsculas en elementos existentes de la base de datos. |
| **LLaMA 3.1** | Ejecución Local | Privacidad y soberanía de los datos al no depender de servicios externos. | Mayor latencia de inferencia y dificultad para seleccionar el nombre exacto de las funciones sin un *prompt* muy estricto. |

### Conclusiones y Retos Técnicos
1. **Ambigüedad en Herramientas:** Modelos locales pequeños tienden a cometer fallos en la selección de herramientas a menos que se limite estrictamente el espacio de decisión mediante ingeniería de prompts.
2. **Normalización de Entidades:** Dificultad generalizada para emparejar registros en bases de datos cuando el usuario varía entre mayúsculas y minúsculas.
3. **Integridad vs. Usabilidad:** Aunque la interfaz conversacional reduce la curva de aprendizaje, delegar mutaciones transaccionales críticas a la interpretación probabilística de un LLM conlleva riesgos de inconsistencia frente a validaciones tradicionales de formularios.

---

## Tecnologías Utilizadas

* **Lenguaje:** Python
* **Modelos e Integraciones:** Google Gemini API (Cloud), Meta LLaMA 3.1 (Local)
* **Arquitectura de Herramientas:** Gemini Function Calling con esquemas JSON
* **Lógica y Persistencia:** Funciones CRUD personalizadas y gestión de estados de stock
* **Visualización:** Librerías de generación de gráficas en Python

---

*Departamento de Lenguajes y Ciencias de la Computación (LCC), Universidad de Málaga (UMA)*
