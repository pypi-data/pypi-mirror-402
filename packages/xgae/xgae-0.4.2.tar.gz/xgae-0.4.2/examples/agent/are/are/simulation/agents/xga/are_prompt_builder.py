import re
from typing import Optional, List, Literal

from xgae.engine.prompt_builder import XGAPromptBuilder
from xgae.utils.misc import read_file


class XGAArePromptBuilder(XGAPromptBuilder):
    def __init__(self, general_system_prompt: Optional[str]):
        are_system_prompt = self.build_are_system_prompt(general_system_prompt)
        super().__init__(are_system_prompt)


    def build_are_system_prompt(self, _system_prompt: str)-> str:
        pattern = r'<general_instructions>(.*?)</general_instructions>'
        prompt_are_general = re.search(pattern, _system_prompt, re.DOTALL)
        prompt_header = "# CORE IDENTITY\n"
        if prompt_are_general:
            prompt_are_general = prompt_header + prompt_are_general.group(1).strip() + "\n\n"
        else:
            prompt_are_general = prompt_header + _system_prompt  + "\n\n"

        are_tool_prompt = read_file("templates/are_prompt_template.md")
        are_system_prompt = prompt_are_general + are_tool_prompt

        return are_system_prompt

