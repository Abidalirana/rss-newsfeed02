import asyncio
from myagents.mainagent import run_pipeline  # import the coroutine

async def main():
    try:
        await run_pipeline()
        print("✅ Agent pipeline finished successfully.")
    except Exception as e:
        print(f"❌ Error occurred while running agent: {e}")

if __name__ == "__main__":
    asyncio.run(main())
