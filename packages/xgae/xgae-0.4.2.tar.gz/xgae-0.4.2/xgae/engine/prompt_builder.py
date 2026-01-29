import json
import datetime

from typing import Optional, List

from xgae.engine.engine_base import XGAToolSchema
from xgae.utils.misc import read_file, format_file_with_args


class XGAPromptBuilder():
    def __init__(self, system_prompt: Optional[str] = None):
        self.system_prompt = system_prompt
        self.prompt_builder_type = "system" if system_prompt else "general"


    def build_task_prompt(self,
                          model_name: str,
                          system_tool_schemas: List[XGAToolSchema],
                          general_tool_schemas: List[XGAToolSchema],
                          custom_tool_schemas: List[XGAToolSchema],
                          agent_tool_schemas: List[XGAToolSchema])-> str:
        if self.system_prompt is None:
            if general_tool_schemas and len(general_tool_schemas) > 0:
                self.system_prompt = self._load_general_prompt(model_name)
            else:
                system_prompt = read_file("templates/system_prompt_template.md")
                self.system_prompt = "#System Prompt" + "\n" + system_prompt
                self.prompt_builder_type = "system"
            task_prompt = self.system_prompt
        else:
            system_tool_prompt = read_file("templates/system_prompt_template.md")
            task_prompt = self.system_prompt + "\n" + system_tool_prompt

        if self.prompt_builder_type == "system":
            system_tool_prompt = ""
            general_tool_prompt = self.build_mcp_tool_prompt(general_tool_schemas)
            general_example_prompt = ""
        else:
            system_tool_prompt, _= self.build_openai_tool_prompt(system_tool_schemas)
            general_tool_prompt, general_example_prompt = self.build_openai_tool_prompt(general_tool_schemas)

        custom_tool_prompt = self.build_mcp_tool_prompt(custom_tool_schemas)
        agent_tool_prompt = self.build_mcp_tool_prompt(agent_tool_schemas)

        if self.prompt_builder_type == "system":
            task_prompt = task_prompt.replace("<<general_tool_schemas>>", general_tool_prompt)
            task_prompt = task_prompt.replace("<<custom_tool_schemas>>", custom_tool_prompt)
            task_prompt = task_prompt.replace("<<agent_tool_schemas>>", agent_tool_prompt)
        else:
            task_prompt = task_prompt.replace("<<system_tool_schemas>>", system_tool_prompt)
            task_prompt = task_prompt.replace("<<general_tool_schemas>>", general_tool_prompt)
            task_prompt = task_prompt.replace("<<general_tool_examples>>", general_example_prompt)
            task_prompt = task_prompt.replace("<<custom_tool_schemas>>", custom_tool_prompt)
            task_prompt = task_prompt.replace("<<agent_tool_schemas>>", agent_tool_prompt)

        return task_prompt


    def build_openai_tool_prompt(self, tool_schemas:List[XGAToolSchema]):
        tool_schemas = tool_schemas or []
        example_prompt = ""
        schema_prompt = ""

        if len(tool_schemas) > 0:
            example_prompt = ""
            openai_schemas = []
            for tool_schema in tool_schemas:
                openai_schema = {}
                openai_function = {}
                openai_schema['type'] = "function"
                openai_schema['function'] = openai_function

                openai_function['name'] = tool_schema.tool_name
                openai_function['description'] = tool_schema.description if tool_schema.description else 'No description available'
                openai_parameters = {}
                openai_function['parameters'] = openai_parameters

                input_schema = tool_schema.input_schema
                openai_parameters['type']       = input_schema['type']
                openai_parameters['properties'] = input_schema.get('properties', {})
                openai_parameters['required']   = input_schema['required']

                openai_schemas.append(openai_schema)

                metadata = tool_schema.metadata or {}
                example = metadata.get("example", None)
                if example:
                    example_prompt += f"\n{example}\n"

            schema_prompt = json.dumps(openai_schemas, ensure_ascii=False, indent=2)

        return schema_prompt, example_prompt


    def build_mcp_tool_prompt(self, tool_schemas:List[XGAToolSchema])-> str:
        tool_schemas = tool_schemas or []
        schema_prompt = ""

        if len(tool_schemas) > 0:
            for tool_schema in tool_schemas:
                description = tool_schema.description if tool_schema.description else 'No description available'
                schema_prompt += f"- {tool_schema.tool_name}: {description}\n"
                parameters = tool_schema.input_schema.get('properties', {})
                schema_prompt += f"   Parameters: {parameters}\n"
                schema_prompt += "\n"

        return schema_prompt


    def _load_general_prompt(self, model_name) -> Optional[str]:
        # TODO: Future
        # if "gemini-2.5-flash" in model_name.lower() and "gemini-2.5-pro" not in model_name.lower():
        #     system_prompt_template = read_file("templates/gemini_system_prompt_template.txt")
        # else:
        #     system_prompt_template = read_file("templates/general_prompt_template.md")

        system_prompt_template = read_file("templates/general_prompt_template.md")
        system_prompt = format_file_with_args(system_prompt_template, {"datetime": datetime})

        system_prompt = system_prompt.format(
            current_date=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d'),
            current_time=datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S'),
            current_year=datetime.datetime.now(datetime.timezone.utc).strftime('%Y')
        )

        # TODO: Future
        # if "anthropic" in model_name.lower():
        #     sample_response = read_file("templates/anthropic_response_sample.txt")
        #     system_prompt = system_prompt + "\n\n <sample_assistant_response>" + sample_response + "</sample_assistant_response>"

        return system_prompt


if __name__ == "__main__":
    import asyncio
    from xgae.engine.mcp_tool_box import XGAMcpToolBox
    from xgae.utils.setup_env import setup_logging

    setup_logging()

    async def main():
        ## Before Run Exec: uv run example-fault-tools
        mcp_tool_box = XGAMcpToolBox(custom_mcp_server_file="xga_mcp_servers.json")
        task_id = "task1"
        await mcp_tool_box.init_tool_schemas()
        await mcp_tool_box.creat_task_tool_box(task_id=task_id, general_tools=["*"], custom_tools=["*"])

        system_tool_schemas = mcp_tool_box.get_task_tool_schemas(task_id, "system")
        general_tool_schemas = mcp_tool_box.get_task_tool_schemas(task_id, "general")
        custom_tool_schemas = mcp_tool_box.get_task_tool_schemas(task_id, "custom")
        agent_tool_schemas = mcp_tool_box.get_task_tool_schemas(task_id, "agent")

        #system_prompt = read_file("templates/example/fault_user_prompt.md")
        system_prompt = None

        prompt_builder = XGAPromptBuilder(system_prompt)
        task_prompt = prompt_builder.build_task_prompt(model_name="openai/qwen-plus",
                                         system_tool_schemas=system_tool_schemas,
                                         general_tool_schemas=general_tool_schemas,
                                         custom_tool_schemas=custom_tool_schemas,
                                         agent_tool_schemas=agent_tool_schemas)

        print(task_prompt)


    asyncio.run(main())