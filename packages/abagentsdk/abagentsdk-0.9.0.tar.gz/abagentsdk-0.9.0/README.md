# ================================
# 🚀 ABZ Agent SDK Quick Start Guide
# ================================

# 1️⃣ Install ABZ Agent SDK
pip install abagentsdk
# or
uv add abagentsdk

# 2️⃣ Create a .env file and add your keys
echo "GEMINI_API_KEY=your_gemini_key_here" >> .env
echo "GROQ_API_KEY=your_groq_key_here" >> .env
# 3️⃣ Create a new Python file (app.py)
# ------------------------------------
from dotenv import load_dotenv
load_dotenv()
import os
from abagentsdk import Agent, Memory

# Load API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# Create an Agent
agent = Agent(
    name="Assistant Agent",
    instructions="You are a helpful assistant.",
    model="qwen/qwen3-32b",
    memory=Memory(),
)

# Run the Agent in a chat loop
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break
    response = agent.run(user_input)
    print("Agent:", response.content)

# 4️⃣ Run your agent
python app.py

