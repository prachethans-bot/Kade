import random
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    AgentServer,
    AgentSession,
    Agent,
    inference,
    room_io,
    TurnHandlingOptions,
)
from livekit.plugins import ai_coustics

from tools import get_weather,send_email

load_dotenv(".env.local")
from mem0 import MemoryClient

client = MemoryClient(api_key="m0-ivv6SPaZVI9I7OoSYUSqzn842hTozmyy2uy0n5LV")

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are Kade, a helpful voice AI assistant and AI partner.

You are straight forward, confident, casual, witty, and occasionally sarcastic.
You should sound natural and human, not robotic or overly formal.
Be concise and get straight to the point.
You can make jokes and use light humor when appropriate.
Do not force jokes into every response.
You can occasionally laugh naturally using phrases like haha or heh.
Be honest and direct instead of unnecessarily polite or vague.
If the user asks something simple, give a simple answer.
If the user needs detailed help, explain it clearly.
Never use complex formatting, emojis, asterisks, or unnecessary symbols in your spoken responses.



You have two tools available:

1. get_weather - use this whenever the user asks about weather, temperature,
   or conditions in any city. Just call it with the city name.

2. send_email - use this when the user asks you to send an email.
   Before calling this tool you MUST have three things: the recipient's
   email address, a subject, and a body. If the user hasn't given you all
   three, ask for whatever is missing before sending. Confirm back to the
   user once the email has been sent.
""",
            tools=[get_weather, send_email],
        )


server = AgentServer()


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: agents.JobContext):

    session = AgentSession(
        stt=inference.STT(
            model="deepgram/nova-3",
            language="multi",
        ),
        llm=inference.LLM(
            model="google/gemini-2.5-flash",
        ),
        tts=inference.TTS(
            model="inworld/inworld-tts-2",
            voice="Ashley",
        ),
        turn_handling=TurnHandlingOptions(
            turn_detection=inference.TurnDetector(),
        ),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_options=room_io.RoomOptions(
            video_input=True,
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=ai_coustics.audio_enhancement(
                    model=ai_coustics.EnhancerModel.QUAIL_VF_S,
                ),
            ),
        ),
    )

    welcome_messages = [
        "Hi there, it's Kade. I'm your AI partner. How can I assist you?",
        "Yo, Kade here. Your AI partner has arrived. What's up?",
        "Hey there, it's Kade. What are we working on today?",
        "What's up? Kade here. Tell me what you need and let's get it done.",
        "Hey, it's Kade. I'm ready. What's the mission today?",
        "Kade here. Your AI partner, fully awake and ready to help. What do you need?",
        "Hey there. Kade's online. Hit me with your question.",
        "Well, look who showed up. Kade here. What are we getting into today? Haha.",
        "Hey, it's Kade. Don't be shy. Ask me something interesting.",
        "Kade here. Let's skip the boring stuff. What do you need?",
    ]
    messages = [
        { "role": "user", "content": "Hi, I'm Prachethan. I'm a vegetarian and I'm allergic to nuts." },
        { "role": "assistant", "content": "Hello Prachethan! I see that you're a vegetarian with a nut allergy." }
    ]

    client.add(messages, user_id="prachethan")
    query = "What can I cook for dinner tonight?"
    client.search(query, filters={"user_id": "prachethan"})


if __name__ == "__main__":
    agents.cli.run_app(server)