# Standard library imports
import dataclasses
from typing import Optional

# Third party imports
from jinja2 import Template


@dataclasses.dataclass
class Turn:
    prompt: str
    response: str


def render_messages_template(
    prompt: str, template: Template, system_prompt: Optional[str] = None, turns: list[Turn] = []
) -> str:
    return template.render(
        system_prompt=system_prompt,
        prompt=prompt,
        turns=[dataclasses.asdict(turn) for turn in turns],
    )
