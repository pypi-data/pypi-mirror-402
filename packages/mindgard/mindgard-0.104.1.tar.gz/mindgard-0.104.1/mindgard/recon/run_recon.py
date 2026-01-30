# Standard library imports
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from typing import Any

# Third party imports
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Project imports
from mindgard.api.exceptions import ClientException
from mindgard.api.recon.recon import ReconClient, ReconResult
from mindgard.auth import load_access_token
from mindgard.constants import API_BASE, DASHBOARD_URL
from mindgard.recon.constants import recon_constants
from mindgard.recon.recon_subcommand import ReconCommand
from mindgard.utils import CliResponse
from mindgard.wrappers.llm import LLMModelWrapper


def run_recon(type: str, console: Console, model_wrapper: LLMModelWrapper, final_args: dict[str, Any]):
    access_token = load_access_token()
    recon_service = ReconClient(API_BASE, access_token, final_args["project_id"])
    recon_command = ReconCommand(recon_service, model_wrapper, type)
    result: ReconResult = None

    def recon() -> None:
        nonlocal result
        recon_id = recon_command.start_recon(final_args["project_id"])
        recon_command.poll_recon(recon_id)
        result = recon_command.fetch_recon_result(recon_id)

    def recon_with_spinner() -> None:
        with Progress(
            SpinnerColumn(style="bold yellow"),
            TextColumn("[bold yellow]Probing target…"),
            transient=True,
            console=console,
        ) as progress:
            task_id = progress.add_task("probing", total=None)

            with ThreadPoolExecutor(max_workers=1) as executor:
                recon_future = executor.submit(recon)

                while not recon_future.done():
                    sleep(0.15)

                progress.update(task_id, completed=100)
                recon_future.result()

    # Helper to map recon type to constant name for dashboard link
    def reverse_lookup(type: str) -> str:
        for key, value in recon_constants._asdict().items():
            if value == type:
                return key
        return "unknown"

    try:
        recon_with_spinner()
    except ClientException as ex:
        raise ex

    if result is None:
        console.print(f"Failed to get result from {type} recon session")
        exit(CliResponse(1).code())

    console.print("\nProbing completed!", style="bold green")
    detected = result.result.total_detected > 0

    if not detected:
        console.print(f"\nNo clear signs of {type} from target system.", style="bold red")
        console.print(
            f"\n[underline]Reasoning[/underline]: The target didn't produce outputs that point to a successful {type}."
        )
        console.print(
            f"[underline]Recommendation[/underline]: Run the complete mindgard test suite for open-ended probing to uncover any additional risks. See [yellow]mindgard test --help[/yellow] to learn more.\n"
        )
        exit(CliResponse(0).code())

    console.print(
        f"\nFull results can be found here: {DASHBOARD_URL}/results/recon?project_id={result.project_id}&reconType={reverse_lookup(type)}\n"
    )
