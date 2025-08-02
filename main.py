# main.py
import asyncio
from myagents.mainagent import run_main_agent  # uses the alias you just exported

async def main():
    try:
        await run_main_agent()
        print("✅ Agent pipeline finished successfully.")
    except Exception as e:
        print(f"❌ Error occurred while running agent: {e}")

if __name__ == "__main__":
    asyncio.run(main())
