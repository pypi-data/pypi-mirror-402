# Standard library imports
import json
import logging
import random
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple

# Third party imports
import requests
from rich.console import Console

# Project imports
from mindgard.wrappers.llm import (
    AnthropicWrapper,
    APIModelWrapper,
    AzureAIStudioWrapper,
    AzureOpenAIWrapper,
    Context,
    HuggingFaceWrapper,
    LLMModelWrapper,
    OpenAIWrapper,
    PromptResponse,
    TestStaticResponder,
)

logger = logging.getLogger(__name__)


class CheckStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"


@dataclass
class CompatCheckResult:
    """Result of a single compatibility check."""

    name: str
    status: CheckStatus
    message: str
    details: Optional[str] = None


@dataclass
class CompatReport:
    """Full compatibility report containing all check results."""

    # Wrapper checks
    openai_static: CompatCheckResult
    openai_runtime: CompatCheckResult

    # Technique checks
    session_memory: CompatCheckResult
    session_isolation: CompatCheckResult
    session_overwriting: CompatCheckResult

    @property
    def all_passed(self) -> bool:
        """Check if all non-skipped checks passed."""
        results = [
            self.openai_static,
            self.openai_runtime,
            self.session_memory,
            self.session_isolation,
            self.session_overwriting,
        ]
        # A check counts as "passed" if it's PASS or SKIP
        return all(r.status in (CheckStatus.PASS, CheckStatus.SKIP) for r in results)


CONVERSATION_CAPABLE_WRAPPERS = (
    OpenAIWrapper,
    AzureOpenAIWrapper,
    AnthropicWrapper,
    TestStaticResponder,
)

SINGLE_TURN_WRAPPERS = (
    APIModelWrapper,
    HuggingFaceWrapper,
    AzureAIStudioWrapper,
)

OPENAI_URL_PATTERNS = [
    r".*/v1/chat/completions/?$",
    r".*/chat/completions/?$",
]


def _test_phrase_1() -> str:
    return "carrot-apple"


def _test_phrase_2() -> str:
    return "yam-strawberry"


def check_openai_static(wrapper: LLMModelWrapper) -> CompatCheckResult:
    """
    Static check: Determine if the wrapper class supports conversations.

    This checks the wrapper TYPE, not runtime behavior.
    """
    wrapper_type = type(wrapper).__name__

    if isinstance(wrapper, CONVERSATION_CAPABLE_WRAPPERS):
        return CompatCheckResult(
            name="OpenAI Static Check",
            status=CheckStatus.PASS,
            message=f"Wrapper '{wrapper_type}' supports conversations",
            details="This wrapper builds message arrays with conversation history",
        )

    if isinstance(wrapper, SINGLE_TURN_WRAPPERS):
        return CompatCheckResult(
            name="OpenAI Static Check",
            status=CheckStatus.FAIL,
            message=f"Wrapper '{wrapper_type}' does not support conversations",
            details="This wrapper sends prompts without conversation history",
        )

    # Unknown wrapper type
    return CompatCheckResult(
        name="OpenAI Static Check",
        status=CheckStatus.FAIL,
        message=f"Unknown wrapper type '{wrapper_type}' - cannot determine conversation support",
        details="Consider using a known preset (openai, anthropic, azure-openai)",
    )


def _url_matches_openai_pattern(url: Optional[str]) -> bool:
    """Check if URL matches OpenAI-style chat completion endpoint pattern."""
    if not url:
        return False
    for pattern in OPENAI_URL_PATTERNS:
        if re.match(pattern, url, re.IGNORECASE):
            return True
    return False


def _try_openai_request(url: str, headers: Optional[Dict[str, str]] = None) -> Tuple[bool, Optional[str]]:
    """
    Try sending an OpenAI-style chat completion request to the URL.

    Returns (is_openai_compatible, response_content_or_error)
    """
    payload = {"messages": [{"role": "user", "content": "hello!"}]}

    try:
        response = requests.post(url, json=payload, headers=headers or {}, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Check for OpenAI-style response structure
        if "choices" in data and isinstance(data["choices"], list) and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if "message" in choice and "content" in choice.get("message", {}):
                content = choice["message"]["content"]
                return True, content

        return False, "Response does not match OpenAI chat completion format"
    except requests.exceptions.Timeout:
        return False, "Request timed out"
    except requests.exceptions.ConnectionError as e:
        return False, f"Connection error: {str(e)}"
    except requests.exceptions.HTTPError as e:
        return False, f"HTTP error: {e.response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def check_openai_runtime(
    wrapper: LLMModelWrapper,
    url: Optional[str],
    headers: Optional[Dict[str, str]] = None,
) -> CompatCheckResult:
    """
    Check if a URL that looks like OpenAI endpoint is actually OpenAI-compatible.
    """
    # Skip if already using an OpenAI-compatible wrapper
    if isinstance(wrapper, (OpenAIWrapper, AzureOpenAIWrapper)):
        return CompatCheckResult(
            name="OpenAI Runtime Check",
            status=CheckStatus.SKIP,
            message="Already using OpenAI-compatible wrapper",
            details=None,
        )

    # Check if URL matches OpenAI pattern
    if url is None or not _url_matches_openai_pattern(url):
        return CompatCheckResult(
            name="OpenAI Runtime Check",
            status=CheckStatus.SKIP,
            message="URL does not match OpenAI pattern",
            details="URL pattern check only applies to endpoints like */v1/chat/completions",
        )

    # URL matches pattern - try an actual request
    is_compatible, result = _try_openai_request(url, headers)

    if is_compatible:
        fixed_url = url.replace("/v1/chat/completions", "")
        return CompatCheckResult(
            name="OpenAI Runtime Check",
            status=CheckStatus.PASS,
            message="URL appears to be OpenAI-compatible!",
            details=f"Recommendation: Use --preset openai-compatible and '{fixed_url}' url instead for better conversation support",
        )
    else:
        return CompatCheckResult(
            name="OpenAI Runtime Check",
            status=CheckStatus.FAIL,
            message="URL matches OpenAI pattern but endpoint is not compatible",
            details=result,
        )


def check_session_is_appendable(
    wrapper: LLMModelWrapper,
) -> CompatCheckResult:
    """
    Session memory check: Send a 2-turn conversation and verify the second turn
    receives the context from the first turn.

    Uses an "echo test" pattern:
    Turn 1: Ask the model to remember a unique phrase
    Turn 2: Ask the model to recall the phrase
    """
    test_phrase = _test_phrase_1()

    turn1_prompt = f"I'm going to tell you a made-up phrase. Please remember it exactly. The phrase is: {test_phrase}. Just acknowledge you received it."
    turn2_prompt = "What was the phrase I just told you? Please respond with ONLY the phrase, nothing else."

    context = Context()

    try:
        logger.debug(f"Session memory check - Turn 1: {turn1_prompt}")
        response1 = wrapper(turn1_prompt, with_context=context)
        logger.debug(f"Turn 1 response: {response1.response}")

        logger.debug(f"Session memory check - Turn 2: {turn2_prompt}")
        response2 = wrapper(turn2_prompt, with_context=context)
        logger.debug(f"Turn 2 response: {response2.response}")

        if test_phrase in response2.response.lower():
            return CompatCheckResult(
                name="Session Memory",
                status=CheckStatus.PASS,
                message="Model correctly recalled information from previous turn",
                details=f"Test phrase '{test_phrase}' was successfully echoed back",
            )
        else:
            return CompatCheckResult(
                name="Session Memory",
                status=CheckStatus.FAIL,
                message="Model did NOT recall information from previous turn",
                details=f"Expected '{test_phrase}' in response, got: '{response2.response[:100]}...'",
            )

    except NotImplementedError as e:
        return CompatCheckResult(
            name="Session Memory",
            status=CheckStatus.FAIL,
            message="Wrapper raised NotImplementedError for conversations",
            details=str(e),
        )
    except Exception as e:
        logger.error(f"Session memory check failed with exception: {e}")
        return CompatCheckResult(
            name="Session Memory",
            status=CheckStatus.ERROR,
            message=f"Error during session memory check: {type(e).__name__}",
            details=str(e),
        )


def check_session_is_reset(
    wrapper: LLMModelWrapper,
) -> CompatCheckResult:
    """
    Session isolation check: Test if the target model has persistent memory across
    SEPARATE conversation contexts.

    This checks if the model retains information from a PREVIOUS context
    when asked in a NEW context (i.e., no explicit context passed).

    Most models should NOT have this - it would indicate shared state.
    """
    test_phrase = _test_phrase_1()

    setup_prompt = f"Remember this phrase for later: {test_phrase}. Just say 'Noted' to confirm."
    recall_prompt = "Do you remember any fruit-vegetable phrase I mentioned recently? If yes, what is it? If no, say 'No memory of that'."

    try:
        # Context 1: Store the code word
        context1 = Context()
        logger.debug(f"Session isolation check - Setup in context1: {setup_prompt}")
        response1 = wrapper(setup_prompt, with_context=context1)
        logger.debug(f"Setup response: {response1.response}")

        # Context 2 (NEW, separate context): Try to recall
        context2 = Context()
        logger.debug(f"Session isolation check - Recall in new context2: {recall_prompt}")
        response2 = wrapper(recall_prompt, with_context=context2)
        logger.debug(f"Recall response: {response2.response}")

        # If the phrase appears, model has unexpected persistent memory
        if test_phrase in response2.response.lower():
            return CompatCheckResult(
                name="Session Isolation",
                status=CheckStatus.FAIL,
                message="WARNING: Model has persistent memory across sessions!",
                details="The model remembered information from a previous session - this may indicate shared state",
            )
        else:
            return CompatCheckResult(
                name="Session Isolation",
                status=CheckStatus.PASS,
                message="Model does NOT appear to have persistent memory across sessions",
                details="Fresh sessions start without previous conversation history",
            )

    except Exception as e:
        logger.error(f"Session isolation check failed with exception: {e}")
        return CompatCheckResult(
            name="Session Isolation",
            status=CheckStatus.ERROR,
            message=f"Error during session isolation check: {type(e).__name__}",
            details=str(e),
        )


def check_session_is_overwritable(
    wrapper: LLMModelWrapper,
) -> CompatCheckResult:
    """
    Assert that the CLI can send the target a user-assistant message history and have the target abide by this.
    Implies full control over the targets history.

    Dummy Turn 1: The user sends a message
    Dummy Turn 2: The target response is mocked with an embedded phrase
    Dummy Turn 3: The user sends another message asking the target repeat its previous message
    Turn 4: The target responds with something containing the embedded phrase

    <same session>

    Dummy Turn 1: The user sends a message
    Dummy Turn 2: The target response is mocked with an embedded phrase
    Dummy Turn 3: The user sends another message asking the target repeat its previous message
    Turn 4: The target responds with something containing the embedded phrase
    """

    initial_user_prompt = "What's the capital of France?"
    assistant_response_template = "The capital of France is {test_phrase}."
    follow_up_user_prompt = "What was your last message to me?"

    pre_overwrite_test_phrase = _test_phrase_1()
    post_overwrite_test_phrase = _test_phrase_2()

    context = Context()
    context.add(
        PromptResponse(
            prompt=initial_user_prompt,
            response=assistant_response_template.format(test_phrase=pre_overwrite_test_phrase),
            duration_ms=0.0,
        )
    )

    try:
        assistant_r1 = wrapper(follow_up_user_prompt, with_context=context)

        if pre_overwrite_test_phrase in assistant_r1.response.lower():

            context.turns = []
            context.add(
                PromptResponse(
                    prompt=initial_user_prompt,
                    response=assistant_response_template.format(test_phrase=post_overwrite_test_phrase),
                    duration_ms=0.0,
                )
            )

            assistant_r2 = wrapper(follow_up_user_prompt, with_context=context)

            if post_overwrite_test_phrase in assistant_r2.response.lower():
                return CompatCheckResult(
                    name="History overwriting",
                    status=CheckStatus.PASS,
                    message="Model had its history overwritten",
                    details=f"Test phrase '{post_overwrite_test_phrase}' was successfully echoed back after overwriting test phrase '{pre_overwrite_test_phrase}'.",
                )
            else:
                return CompatCheckResult(
                    name="History overwriting step 2",
                    status=CheckStatus.FAIL,
                    message="Model did not have its history overwritten successfully",
                    details=f"Expected '{post_overwrite_test_phrase}' in response, got: '{assistant_r1.response[:100]}...'",
                )

        else:
            return CompatCheckResult(
                name="History overwriting step 1",
                status=CheckStatus.FAIL,
                message="Model has could not remember initial test phrase making overwriting impossible",
                details=f"Expected '{pre_overwrite_test_phrase}' in response, got: '{assistant_r1.response[:100]}...'",
            )

    except NotImplementedError as e:
        return CompatCheckResult(
            name="History overwriting",
            status=CheckStatus.FAIL,
            message="Wrapper raised NotImplementedError for conversations",
            details=str(e),
        )
    except Exception as e:
        logger.error(f"History overwriting check failed with exception: {e}")
        return CompatCheckResult(
            name="History overwriting",
            status=CheckStatus.ERROR,
            message=f"Error during session memory check: {type(e).__name__}",
            details=str(e),
        )


def run_compat_checks(
    wrapper: LLMModelWrapper,
    url: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    skip_runtime: bool = False,
) -> CompatReport:
    """
    Run all compatibility checks and return a full report.

    Args:
        wrapper: The LLM model wrapper to test
        console: Rich console for output
        url: The target URL (for OpenAI runtime check)
        headers: Request headers (for OpenAI runtime check)
        json_out: Whether to output in JSON format
        skip_runtime: Skip runtime tests (only do static checks)

    Returns:
        CompatReport with results of all checks
    """
    # Wrapper checks
    # 1. OpenAI static check (always runs)
    openai_static_result = check_openai_static(wrapper)

    # 2. OpenAI runtime check (runs if URL matches pattern)
    openai_runtime_result = check_openai_runtime(wrapper, url, headers)

    # Technique checks
    # 3. Session memory check
    if skip_runtime:
        session_memory_result = CompatCheckResult(
            name="Session Memory",
            status=CheckStatus.SKIP,
            message="Skipped (--skip-runtime flag)",
            details=None,
        )
    elif openai_static_result.status == CheckStatus.FAIL and openai_runtime_result.status != CheckStatus.PASS:
        # If static check failed AND OpenAI runtime didn't find a compatible endpoint,
        # skip session memory check (it will fail anyway)
        session_memory_result = CompatCheckResult(
            name="Session Memory",
            status=CheckStatus.SKIP,
            message="Skipped (static check failed)",
            details="Session memory check skipped because wrapper doesn't support conversations",
        )
    else:
        session_memory_result = check_session_is_appendable(wrapper)

    # 4. Session isolation check
    if skip_runtime:
        session_isolation_result = CompatCheckResult(
            name="Session Isolation",
            status=CheckStatus.SKIP,
            message="Skipped (--skip-runtime flag)",
            details=None,
        )
    else:
        session_isolation_result = check_session_is_reset(wrapper)

    if skip_runtime:
        session_overwritable_result = CompatCheckResult(
            name="History overwriting", status=CheckStatus.SKIP, message="Skipped (--skip-runtime flag)", details=None
        )
    else:
        session_overwritable_result = check_session_is_overwritable(wrapper)

    return CompatReport(
        openai_static=openai_static_result,
        openai_runtime=openai_runtime_result,
        session_memory=session_memory_result,
        session_isolation=session_isolation_result,
        session_overwriting=session_overwritable_result,
    )
