# src/crew_runner.py

import os
import asyncio
from crewai import Agent, Task, Crew
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters

# -------------------------------
# 1) Configurar parámetros MCP
# -------------------------------
# En este MVP vamos a arrancar un servidor MCP local para que CrewAI lo use.
# Asumimos que tienes un script en servers/simple_mcp_server.py que lanza un MCP de Gemini.
# Si no, puedes usar directamente el servidor MCP que CrewAI levanta por defecto al no usar MCPServerAdapter.

# (Opcional) Si quieres conectar con un servidor MCP externo:
# airtable_mcp_params = StdioServerParameters(
#     command="python3",
#     args=["servers/airtable_mcp_server.py"],
#     env={
#         "AIRTABLE_API_KEY": os.getenv("AIRTABLE_API_KEY", ""),
#         "AIRTABLE_BASE_ID": os.getenv("AIRTABLE_BASE_ID", ""),
#         **os.environ
#     },
# )

# Para este MVP omitimos MCP externo de Airtable. CrewAI correrá sus agentes directamente.

# -------------------------------
# 2) Crear Agentes en código
#    (Se basearán en la configuración de config/agents.yaml)
# -------------------------------
conversational_agent = Agent.from_yaml(
    name="conversational_agent",
    yaml_path="config/agents.yaml"
)

lead_qualifier_agent = Agent.from_yaml(
    name="lead_qualifier_agent",
    yaml_path="config/agents.yaml"
)

atm_agent = Agent.from_yaml(
    name="atm_agent",
    yaml_path="config/agents.yaml"
)

# -------------------------------
# 3) Crear Tareas en código
#    (Se basan en config/tasks.yaml)
# -------------------------------
conversation_task = Task.from_yaml(
    name="conversation_task",
    yaml_path="config/tasks.yaml"
)

qualification_task = Task.from_yaml(
    name="qualification_task",
    yaml_path="config/tasks.yaml"
)

airtable_registration_task = Task.from_yaml(
    name="airtable_registration_task",
    yaml_path="config/tasks.yaml"
)

# -------------------------------
# 4) Instanciar Crew
# -------------------------------
lead_management_crew = Crew(
    agents=[conversational_agent, lead_qualifier_agent, atm_agent],
    tasks=[conversation_task, qualification_task, airtable_registration_task],
    verbose=True,
    memory=True
)

# -------------------------------
# 5) Funciones públicas
# -------------------------------
async def run_conversation(message: str):
    """Run a single conversational turn with the conversational_agent."""
    task = Task(
        description="Responde al usuario de forma cordial al mensaje: {message}",
        expected_output="Respuesta del agente",
        agent=conversational_agent,
    )

    crew = Crew(
        agents=[conversational_agent],
        tasks=[task],
        verbose=True,
        memory=True,
    )

    result = await crew.kickoff(inputs={"message": message})
    return result


# -------------------------------
# 6) Función para arrancar el flujo completo de lead
# -------------------------------
async def run_lead_flow(lead_name: str, company: str):
    """
    Inputs mínimos: lead_name (nombre del prospecto), company (nombre de la empresa).
    Devuelve el resultado final de la tarea airtable_registration_task.
    """
    inputs = {"lead_name": lead_name, "company": company}
    result = await lead_management_crew.kickoff(inputs=inputs)
    return result

# -------------------------------
# 7) Prueba rápida (solo para correr por consola)
# -------------------------------
if __name__ == "__main__":
    async def main():
        print("🔄 Iniciando flujo de conversación/cualificación de lead...")
        res = await run_lead_flow("John Doe", "TechCorp")
        print("💾 Resultado final:\n", res)

    asyncio.run(main())
