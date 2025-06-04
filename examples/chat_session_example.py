# examples/chat_session_example.py

"""
Ejemplo de ejecución del flujo completo por consola.
"""

import asyncio
from src.crew_runner import run_lead_flow

async def main():
    print("🚀 Simulando flujo para John Doe / TechCorp")
    result = await run_lead_flow("John Doe", "TechCorp")
    print("Resultado final:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
