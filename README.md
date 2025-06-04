# 🧠 Lead Qualifier AI – IA Conversacional para Calificación de Leads

Lead Qualifier AI es una solución inteligente de captura y calificación de leads integrada mediante un widget flotante embebido en cualquier sitio web. Utiliza agentes especializados, técnicas RAG y el protocolo Model Context Protocol (MCP) sobre CrewAI para generar conversaciones personalizadas, estructurar la información obtenida y calificar leads en tiempo real.

---

## 🚀 Tecnologías Utilizadas

- **CrewAI**: Framework para agentes colaborativos multi-rol.
- **Model Context Protocol (MCP)**: Comunicación entre servicios LLM, con múltiples servidores y seguridad integrada.
- **RAG (Retrieval-Augmented Generation)**: Para enriquecer las respuestas de la IA con información almacenada.
- **ChromaDB** *(futuro)*: Vector store para respuestas contextuales.
- **FastAPI**: Backend rápido y asincrónico.
- **HTML/CSS/JS**: Para el widget embebido.
- **Airtable API**: CRM / gestión de leads.

---

## 📂 Estructura del Proyecto

```

.
├── config
│   ├── agents.yaml               # Definición de agentes CrewAI
│   └── tasks.yaml                # Tareas de cada agente
├── frontend
│   └── iframe\_widget
│       ├── index.html            # Widget flotante
│       ├── style.css             # Estilos del widget
│       └── script.js             # Lógica de comunicación con backend
├── src
│   ├── main.py                   # Entrada principal del backend FastAPI
│   ├── crew\_runner.py           # Inicializa y ejecuta los agentes CrewAI
│   ├── extractor.py             # Extrae datos estructurados desde la conversación
│   └── atm\_service.py           # Conecta con Airtable para actualizar leads
├── prompts
│   └── mcp\_lead\_prompt.yaml     # Plantilla de prompt MCP optimizado
├── examples
│   └── chat\_session\_example.py  # Ejemplo local de conversación
├── requirements.txt             # Dependencias del proyecto

```

---

## 🧩 Configuración Inicial

1. **Clona el repositorio** (por SSH):

```
git clone git@github.com:tu_usuario/lead-qualifier-ai.git
cd lead-qualifier-ai
```

2. **Crea y activa el entorno virtual**:

```
pyenv virtualenv 3.11.8 lead-qualifier-env
pyenv local lead-qualifier-env
python -m venv .venv
source .venv/bin/activate
```

3. **Instala dependencias**:

```
pip install -r requirements.txt
```

4. **Configura variables de entorno** (si usas `.env` o secretos):

```
AIRTABLE_API_KEY=```
MCP_API_KEY=```
```

---

## 🔧 Uso del Proyecto

### Iniciar backend
```
uvicorn src.main:app --reload
```

### Probar CrewAI + MCP
```
python src/crew_runner.py
```

### Ver conversación de ejemplo
```
python examples/chat_session_example.py
```

### Ejecutar pruebas con pytest
```
pytest
```

---

## 🔐 Seguridad MCP

- Todos los endpoints deben requerir firma y validación de identidad.
- Consulta `config/mcp_server_config.yaml` para gestionar claves y tokens.

---

## 🎯 Roadmap

- [x] Integración CrewAI y MCP
- [x] Widget embebido básico
- [ ] Soporte multilenguaje
- [ ] RAG conectado a ChromaDB
- [ ] Dashboard de analytics para leads

---

## 📜 Licencia

MIT License. Puedes usar, modificar y distribuir este proyecto con libertad.

---

## 🤝 Créditos

Desarrollado por [Tu Nombre / Equipo] como parte del curso de IA aplicada al desarrollo software. Con la ayuda de Cursor, CrewAI y GPT-4.

