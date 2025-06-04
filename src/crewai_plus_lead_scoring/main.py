#!/usr/bin/env python
import sys

from crewai_plus_lead_scoring.crew import CrewaiPlusLeadScoringCrew


def run():
    # Replace with your inputs, it will automatically interpolate any tasks and agents information
    inputs = {
        "company": "<your_company>",
        "product_name": "<your_product_name>",
        "product_description": "<your_product_description>",
        "icp_description": "<ideal_customer_profile_description>",
        "form_response": "<form_response>",
    }
    CrewaiPlusLeadScoringCrew().crew().kickoff(inputs=inputs)


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "company": "<your_company>",
        "product_name": "<your_product_name>",
        "product_description": "<your_product_description>",
        "icp_description": "<ideal_customer_profile_description>",
        "form_response": "<form_response>",
    }
    try:
        CrewaiPlusLeadScoringCrew().crew().train(
            n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        CrewaiPlusLeadScoringCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "company": "<your_company>",
        "product_name": "<your_product_name>",
        "product_description": "<your_product_description>",
        "icp_description": "<ideal_customer_profile_description>",
        "form_response": "<form_response>",
    }
    try:
        CrewaiPlusLeadScoringCrew().crew().test(
            n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")
