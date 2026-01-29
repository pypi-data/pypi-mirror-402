# Standard library imports
from collections import namedtuple

Recon_commands = namedtuple(
    "Recon_commands",
    [
        "recon",
        "guardrail",
        "input_encoding",
        "output_encoding",
        "non_contextual",
        "output_format_generation",
        "output_rendering_format",
        "code_generation",
        "system_prompt_extraction",
        "tool_discovery",
    ],
)

recon_constants = Recon_commands(
    recon="recon",
    guardrail="guardrail",
    input_encoding="input-encoding",
    output_encoding="output-encoding",
    non_contextual="non-contextual",
    output_format_generation="output-format-generation",
    output_rendering_format="output-rendering-format",
    code_generation="code-generation",
    system_prompt_extraction="system-prompt-extraction",
    tool_discovery="tool-discovery",
)
