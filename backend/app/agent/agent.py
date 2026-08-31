import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.messages import (
    HumanMessage,
    ToolMessage,
)

from app.agent.tools import (
    search_trading_knowledge,
    get_current_crypto_price,
    get_crypto_chart_data,
    analyze_market,
)


load_dotenv()


# ---------------------------------------
# Tools
# ---------------------------------------

tools = [
    search_trading_knowledge,
    get_current_crypto_price,
    get_crypto_chart_data,
    analyze_market,
]


# Create lookup dictionary
tool_map = {
    tool.name: tool
    for tool in tools
}

def extract_text(content):
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []

        for item in content:
            if isinstance(item, dict):
                text = item.get("text")

                if text:
                    text_parts.append(text)

        return "\n".join(text_parts)

    return str(content)

# ---------------------------------------
# Gemini
# ---------------------------------------

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0.2,
)

llm_with_tools = llm.bind_tools(tools)



# ---------------------------------------
# Agent
# ---------------------------------------

async def ask_agent(question: str):

    messages = [
        HumanMessage(
            content=question
        )
    ]

    while True:

        response = await llm_with_tools.ainvoke(
            messages
        )

        # Add Gemini response to conversation
        messages.append(response)

        # -----------------------------------
        # No tool call → final answer
        # -----------------------------------

        if not response.tool_calls:

            return extract_text(response.content)

        # -----------------------------------
        # Execute requested tools
        # -----------------------------------

        for tool_call in response.tool_calls:

            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            print(
                f"\nExecuting tool: {tool_name}"
            )

            print(
                f"Arguments: {tool_args}"
            )

            tool = tool_map.get(tool_name)

            if not tool:

                raise ValueError(
                    f"Unknown tool: {tool_name}"
                )

            # Execute tool
            tool_result = await tool.ainvoke(
                tool_args
            )

            print("Tool executed successfully.")

            # Send result back to Gemini
            messages.append(
                ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call["id"],
                )
            )


# ---------------------------------------
# Test
# ---------------------------------------

if __name__ == "__main__":

    import asyncio

    questions = [
        "What is a liquidity?",
        "What is the current BTC price?",
        "What has BTC done over the last 7 days?",
    ]

    async def main():

        for question in questions:

            print("\n================================")
            print("QUESTION")
            print("================================")

            print(question)

            answer = await ask_agent(
                question
            )

            print("\nFINAL ANSWER:")
            print(answer)

    asyncio.run(main())