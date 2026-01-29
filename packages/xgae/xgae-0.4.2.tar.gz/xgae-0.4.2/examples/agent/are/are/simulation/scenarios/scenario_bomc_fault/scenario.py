# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import datetime
import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
from are.simulation.apps.agent_user_interface import AgentUserInterface
from are.simulation.apps.mcp.mcp_app import MCPApp
from are.simulation.scenarios.scenario import Scenario, ScenarioValidationResult
from are.simulation.scenarios.utils.env_utils import expand_env_vars

from are.simulation.scenarios.utils.registry import register_scenario
from are.simulation.types import EventRegisterer, event_registered

# Set up logger
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()



@register_scenario("scenario_bomc_fault")
class ScenarioBomcFault(Scenario):
    start_time: float | None = datetime.datetime.now().timestamp()
    duration: float | None = None

    def init_and_populate_apps(self, *args, **kwargs) -> None:

        # get apps from the demo
        agui = AgentUserInterface()
        self.apps = [agui]

        # form task from universe params
        self.start_time = datetime.datetime.now().timestamp()

        # Load additional MCP apps from JSON file if specified
        self._load_mcp_apps_from_json()


    def build_events_flow(self) -> None:
        """Define the sequence of events that will occur during the scenario"""

        agui = self.get_typed_app(AgentUserInterface)

        with EventRegisterer.capture_mode():
            # User event: User requests task creation
            event1 = agui.send_message_to_agent(
                content="locate 10.0.0.1 fault and solution",
            ).depends_on(None, delay_seconds=2)

            oracle1 = (
                agui.send_message_to_user(
                    content="Fault Cause: Phone Recharge Application Crash; Solution: Restart Phone Recharge Application",
                )
                .oracle()
                .depends_on(event1, delay_seconds=10)
            )


        self.events = [event1]


    def validate(self, env) -> ScenarioValidationResult:
        """
        Validate that the scenario completed successfully.

        Check that the agent properly interacted with our custom app.
        """
        try:
            aui = env.get_app("AgentUserInterface")
            msg = aui.get_last_message_from_agent()
            content = msg.content
            if "Phone Recharge Application Crash" in content:
                return ScenarioValidationResult(success=True)
            else:
                return ScenarioValidationResult(success=False)
        except Exception as e:
            return ScenarioValidationResult(success=False, exception=e)


    def _load_mcp_apps_from_json(self) -> None:
        """
        Load additional MCP apps from a JSON file specified in the environment variables.

        The JSON file should follow the Claude MCP definition format with a ``mcpServers``
        key containing server configurations. Environment variables in the JSON are
        expanded using the current environment.

        :return: None
        """
        # Get the JSON file path from environment variables
        mcp_apps_json_path = os.environ.get("MCP_APPS_JSON_PATH")

        if not mcp_apps_json_path:
            return

        # Ensure self.apps is initialized
        if not hasattr(self, "apps") or self.apps is None:
            self.apps = []

        try:
            with open(mcp_apps_json_path, "r") as f:
                mcp_config = json.load(f)

            if "mcpServers" not in mcp_config:
                logger.warning(
                    f"No 'mcpServers' key found in MCP apps JSON file: {mcp_apps_json_path}"
                )
                return

            # Create MCP apps from the JSON configuration
            for server_name, server_config in mcp_config["mcpServers"].items():
                mcp_app = self._create_mcp_app(server_name, server_config)
                if mcp_app:
                    self.apps.append(mcp_app)
                    logger.info(f"Added MCP app: {server_name}")

        except Exception as e:
            logger.error(f"Error loading MCP apps from JSON: {e}", exc_info=True)

    def _create_mcp_app(self, name: str, config: dict[str, Any]) -> MCPApp | None:
        """
        Create an MCPApp instance from a server configuration.

        Supports two types of MCP servers:

        1. Local servers with command and arguments
        2. Remote SSE servers with URL and headers

        Environment variables in the configuration are expanded before creating the app.

        :param name: The name of the MCP app
        :type name: str
        :param config: The server configuration from the JSON file
        :type config: dict[str, Any]
        :return: An MCPApp instance or None if creation fails
        :rtype: MCPApp | None
        """
        try:
            # Expand environment variables in the configuration
            expanded_config = expand_env_vars(config, allowed=["HF_TOKEN"])

            # Handle SSE remote servers
            if expanded_config.get("type") == "sse" or "url" in expanded_config:
                return MCPApp(
                    name=name,
                    server_url=expanded_config.get("url"),
                    sse_headers=expanded_config.get("headers", {}),
                )

            # Handle local servers with command and args
            elif "command" in expanded_config:
                return MCPApp(
                    name=name,
                    server_command=expanded_config.get("command"),
                    server_args=expanded_config.get("args", []),
                    server_env=expanded_config.get("env", {}),
                )

            else:
                logger.warning(f"Unsupported MCP server configuration for {name}")
                return None

        except Exception as e:
            logger.error(f"Error creating MCP app {name}: {e}", exc_info=True)
            return None


# Before Run Scenario, should xage project , execute command:
# 1. Vailid Success: uv run example-fault-tools
# 2. Vailid Fail: uv run example-fault-tools --alarmtype 2
if __name__ == "__main__":
    from are.simulation.scenarios.utils.cli_utils import run_and_validate

    run_and_validate(ScenarioBomcFault())
