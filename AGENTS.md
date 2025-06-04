# 🤖 AGENTS.md – Documentación de Agentes Inteligentes (CrewAI)

Este archivo detalla cómo navegar por el sistema multi-agente, qué contiene cada archivo relevante, cómo lanzar pruebas, y cómo asegurar buenas prácticas para escalar y mantener el sistema.

---

## 🔧 Arquitectura de Agentes

El sistema se compone de dos agentes principales:

### 1. `LeadCollectorAgent`
- **Función**: Inicia la conversación con el usuario del widget, presenta los objetivos y recopila información básica (nombre, email, necesidad).
- **Prompt base**: `prompts/mcp_lead_prompt.yaml`
- **Definición YAML**: `config/agents.yaml`
- **Tareas**:
  - Presentarse de forma cordial.
  - Realizar preguntas personalizadas según el cliente.
  - Transmitir la conversación a `LeadQualifierAgent` cuando se cumplan condiciones.

### 2. `LeadQualifierAgent`
- **Función**: Evalúa las respuestas recogidas por el primer agente, decide si el lead está cualificado y extrae la información útil para Airtable.
- **Prompt enriquecido**: Incluye instrucciones de extracción estructurada y criterios de decisión.
- **Tareas**:
  - Identificar intención.
  - Calificar el lead.
  - Extraer datos clave para CRM (nombre, email, necesidad, presupuesto).

---

## 🧬 Estructura del Código Relevante

```

config/
├── agents.yaml         # Define los agentes y sus roles
├── tasks.yaml          # Define las tareas y flujos de conversación

src/
├── crew\_runner.py      # Carga y lanza el equipo de agentes
├── extractor.py        # Transforma la conversación en datos estructurados
├── atm\_service.py      # Lógica de conexión con Airtable API

prompts/
├── mcp\_lead\_prompt.yaml   # Prompt en YAML con contexto e instrucciones

````

---

## 🧪 Comandos para Pruebas Locales

### 1. Lanzar conversación de ejemplo:
```
python examples/chat_session_example.py
```

### 2. Ejecutar agentes en producción (backend API):
```
uvicorn src.main:app --reload
```

### 3. Ejecutar Crew desde terminal con tareas:
```
python src/crew_runner.py
```

---

## ✅ Buenas Prácticas

### ✅ Prompts modulares y versionados
- Mantener los prompts en YAML o Markdown.
- Usar comentarios e identificadores claros de etapa/rol.

### ✅ Separación de responsabilidades
- Cada archivo hace una cosa: prompts, lógica de agente, extracción, conexión API.

### ✅ Tareas desacopladas
- Usa `tasks.yaml` para definir etapas. Así puedes cambiar el flujo sin reescribir código.

### ✅ Registro y trazabilidad
- Añadir logging (nivel INFO/DEBUG) en `crew_runner.py` y `extractor.py`.

### ✅ Uso de MCP seguro
- MCP debe estar configurado con endpoint firmado.
- Añadir validación de origen en `main.py` o el proxy MCP.

---

## 📦 Escalabilidad del Sistema

### 🧠 Agregar un nuevo agente
1. Añade el `Agent` en `config/agents.yaml`.
2. Define su prompt en un archivo `.yaml` o `.md` dentro de `prompts/`.
3. Añade tareas nuevas o asócialas en `config/tasks.yaml`.
4. Llama al agente desde `crew_runner.py` cuando se requiera.

### 🛠 Ejemplo:
Agregar `SupportAgent` para seguimiento post-lead.

```yaml
- id: support_agent
  role: "Gestor de soporte"
  goal: "Guiar al lead una vez está cualificado y ofrecer recursos post contacto"
  backstory: "Eres un experto en servicio postventa para PYMEs."
````

---

## 🤝 Contribuir al Proyecto

1. Crea una nueva rama
   ```
   git checkout -b feature/tu-funcionalidad
   ```

2. Añade tu código siguiendo la estructura y estándares

3. Lanza pruebas locales antes de hacer commit

4. Haz pull request y detalla qué funcionalidades has cambiado o añadido

---

## 📎 Referencias

* [CrewAI – Introduction](https://docs.crewai.com/introduction)
* [CrewAI – MCP Overview](https://docs.crewai.com/mcp/overview)
* [MCP – Security Guide](https://docs.crewai.com/mcp/security)

