import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def get_reply(message: str) -> str:
    return (
        "Thanks for sharing your running goals. "
        "When you're ready, click 'Generate Training Plan' "
        "and I'll build a personalized plan."
    )


def generate_plan(runner: dict) -> str:
    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=f"""
            Create a beginner-friendly 2 week running plan.

            Runner profile:
            {runner}

            Format EXACTLY like:

            Week 1 · Base
            Mon: Easy run
            Wed: Intervals
            Sat: Long run

            Week 2 · Build
            Mon: Easy run
            Wed: Tempo run
            Sat: Long run

            Do not use markdown.
            Do not use bullet points.
            """
        )

        return response.text

    except Exception as e:
        return f"Plan generation failed: {e}"