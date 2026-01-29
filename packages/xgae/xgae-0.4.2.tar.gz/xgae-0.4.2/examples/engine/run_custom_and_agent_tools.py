import asyncio

from xgae.engine.mcp_tool_box import XGAMcpToolBox
from xgae.engine.task_engine import XGATaskEngine
from xgae.utils.misc import read_file

from xgae.utils.setup_env import setup_logging


is_stream = False
if is_stream:
    setup_logging(log_level="ERROR") # only show chunk
else:
    setup_logging()

system_prompt = read_file("templates/example/fault_user_prompt.md")
tool_box = XGAMcpToolBox(custom_mcp_server_file="xga_mcp_servers.json")

# Before Run Exec: uv run example-fault-tools --alarmtype 2  , uv run example-a2a-tools
# If want to use real A2A agent tool, use 'xgaproxy' project run: v run xga-a2a-proxy
async def run_custom_plus_a2a_tools() -> None:
    engine = XGATaskEngine(tool_box=tool_box,
                           custom_tools=["*"],
                           system_prompt=system_prompt
                           )


    user_input =  "locate 10.2.3.4 fault and solution"
    global is_stream
    if is_stream:
        chunks = []
        async for chunk in engine.run_task(task_input={"role": "user", "content": user_input}):
            chunks.append(chunk)
            print(chunk)

        final_result = engine.parse_final_result(chunks)
        print(f"\n\nFINAL_RESULT: {final_result}")
    else:
        final_result = await engine.run_task_with_final_answer(task_input={"role": "user", "content": user_input})
        print(f"\n\nFINAL_RESULT: {final_result}")


# Before run example execute with 'xgatools' project: uv run xgatools
# Before run exec: uv run example-fault-tools --alarmtype 3  , uv run example-a2a-tools
async def run_custom_plus_general_tools() -> None:
    engine = XGATaskEngine(system_prompt=system_prompt,
                           tool_box=tool_box,
                           general_tools=["web_search"],
                           custom_tools=["*"])

    user_input = "locate 10.3.4.5 fault and solution"
    final_result = await engine.run_task_with_final_answer(task_input={"role": "user", "content": user_input})
    print("FINAL RESULT:", final_result)


async def main() -> None:
    #await run_custom_plus_a2a_tools()
    await run_custom_plus_general_tools()

asyncio.run(main())