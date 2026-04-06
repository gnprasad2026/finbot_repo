import os
import sqlite3

from app.tools import tools
from app.tools import get_stock_fundamentals
from app.config import settings
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import InMemorySaver



SYSTEM_PROMPT = """
You are FinBot, an expert equity research analyst with deep knowledge of financial markets,
valuation methodologies, and macroeconomic trends.

## Task
Given a stock ticker or company name, produce a concise, structured analyst brief that helps users evaluate the investment. Do not give buy/sell advice. Present data-driven signals only.

## Rules
1. Gather data before analysis. Never rely on memory for numbers.
2. If a tool fails or returns empty data, state it and proceed.
3. Never fabricate prices, ratios, or news.
4. Always follow the output format.
5. Flag notable risks or red flags.

## Output Format

**[TICKER] — Analyst Brief**
- 📊 **Fundamentals:** price, P/E, market cap, revenue growth (one line)
- 📈 **Valuation Signal:** OVERVALUED / FAIRLY VALUED / UNDERVALUED + reason
- 📰 **News Sentiment:** bullish / neutral / bearish + key headline
- ⚠️ **Key Risks:** 1–2 bullets
- 🧭 **Outlook:** 1–2 sentence synthesis, no advice
"""

SQLITE_DB_PATH = settings.SQLITE_DB_PATH
print(f"SQLITE_DB_PATH : {SQLITE_DB_PATH}")



def run_agent(query: str, thread_id: str, user_id: str):
    result = my_finance_agent_persistent.invoke(
        {"messages": [{"role": "user", "content": query}]},
        {"configurable": {"thread_id": thread_id, "user_id": user_id}}
    )
    messages = result.get(messages,[])
    if not messages:
        return "No response from the agent."
    
    last_msg = messages[-1]
    content = getattr(last_msg,"content","")

    if isinstance(content,str):
        return content
    if isinstance(content,list):
        texts = []
        for item in content:
            if isinstance(item,dict) and item.get("type") == "text":
                texts.append(item.get("text",""))
        return "\n".join(texts)
    return str(content)
    



# AGENT = LLM+MEMORY+TOOLS
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    groq_api_key=settings.GROQ_API_KEY,
    max_tokens=None,
    reasoning_format="parsed",
    timeout=None,
    max_retries=2,
)

tool_augmented_model = llm.bind_tools(tools)

response = tool_augmented_model.invoke("How is NVIDIA doing financially")

for tool_call in response.tool_calls:
    print(f"Tool: {tool_call['name']}")
    print(f"Args: {tool_call['args']}")
    tool_result = get_stock_fundamentals.invoke(tool_call)
    print(tool_result.content)

conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
checkpointer = SqliteSaver(conn)

# my_finance_agent = create_agent(
#     model= llm,
#     tools=tools,
#     system_prompt=SYSTEM_PROMPT,
#     # Adding memory to the agent
#     checkpointer = InMemorySaver()
# )

my_finance_agent_persistent = create_agent(
    llm, 
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
    checkpointer = checkpointer
)
config = {"configurable": {"thread_id": "user-alice-session-1"}}
my_finance_agent_persistent.invoke(
    {"messages": [{"role": "user", "content": "Give me a quick brief on NVDA"}]},
    config
)
my_finance_agent_persistent.invoke(
    {"messages": [{"role": "user", "content": "How does it compare to AMD on valuation?"}]},
    config
)
my_finance_agent_persistent.invoke(
    {"messages": [{"role": "user", "content": "Given both, which has better growth prospects?"}]},
    config
)

