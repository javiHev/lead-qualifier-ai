"""Conversational LeadCollector agent definition."""

from crewai import Agent


def create_agent() -> Agent:
    """Creates the LeadCollector agent using CrewAI."""
    return Agent(
        role="LeadCollector",
        goal=(
            "Iniciar conversaciones cordiales con visitantes del sitio y\n"
            "obtener nombre, email y necesidad principal para la posterior\n"
            "cualificación del lead."
        ),
        backstory=(
            "Eres un especialista en captación de leads para PYMEs. "
            "Tu trato es siempre amable y profesional, y sabes cómo hacer\n"
            "preguntas concisas para recopilar los datos clave."),
        llm="google/gemini-2.0-flash",
        memory=True,
        verbose=True,
        tools=[],
    )
