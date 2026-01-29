## GAIA2 ARE Support
### How to add XGAE to ARE Project
- add xgae==0.3.x to ARE requirements.txt
- uv pip install -r requirements.txt
- Modify ARE 'AgentBuilder' and 'AgentConfigBuilder' class, add "xga" type agent :
  ```
  File: agent_builder.py
      class AgentBuilder:
        def list_agents(self) -> list[str]:
          return ["default", "xga"]
            
        def build():
            ...
            agent_name = agent_config.get_agent_name()
            if agent_name in ["default", "xga"]:
                # add xga agent code
      
  File: agent_config_builder.py
    class AgentConfigBuilder:
        def build():
            if agent_name in["default", "xga"]:
  ```
- Modify ARE 'MCPApp' :
    ```
    File: mcp_app.py
        class MCPApp:
            def _call_tool(self, tool_name: str, **kwargs) -> str:
                try:
                    ...
                    # original code don't support async engine loop
                    from are.simulation.agents.xga.mcp_tool_executor import call_mcp_tool
                    result = call_mcp_tool(self.server_url, tool_name, kwargs, 10)
                    return str(result)
    ```


- Modify ARE .env, add XGAE .env config, refer to env.example 
- Copy XGAE package 'templates' directory to ARE project root  


### Run XGA Agent in ARE
  ```
# Run ARE Code Scenario
uv run are-run -e -s scenario_apps_tutorial -a xga --model openai/qwen3-235b-a22b --provider llama-api --output_dir ./output --log-level INFO

# Run Custom Scenario
uv run example-fault-tools 
uv run are-run -e -s scenario_bomc_fault -a xga --model openai/qwen3-235b-a22b --provider llama-api --output_dir ./output --log-level INFO

# Run HF Scenario Benchmark
uv run are-benchmark run -a xga --dataset ./scenarios --config mini --model openai/deepseek-v3.1 --provider llama-api --output_dir ./output --limit 1 --num_runs 1 --max_concurrent_scenarios 1 --log-level INFO

# Run GUI
uv run are-gui -a xga -s scenario_find_image_file --model openai/qwen3-235b-a22b --provider llama-api --log-level INFO

  ```