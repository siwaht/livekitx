import logging
from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.plugins import deepgram, elevenlabs, openai, silero

load_dotenv()

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)


class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a friendly voice assistant. 
Keep your responses short and conversational. 
Answer questions clearly and help users with their requests."""
        )


async def entrypoint(ctx: JobContext):
    await ctx.connect()
    
    logging.info("Connected to room, starting agent session...")

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-2"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(model="tts-1", voice="alloy"),  # Using OpenAI TTS for testing
    )

    await session.start(
        room=ctx.room,
        agent=SimpleAgent(),
    )
    
    logging.info("Session started, generating initial reply...")

    await session.generate_reply(
        instructions="Greet the user warmly and ask how you can help them today."
    )
    
    logging.info("Initial reply generated")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
