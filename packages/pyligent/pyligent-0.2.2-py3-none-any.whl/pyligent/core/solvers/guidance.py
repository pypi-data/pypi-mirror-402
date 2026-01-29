from __future__ import annotations

from typing import Callable, List, Tuple

import guidance
from loguru import logger

from pyligent.core.path import PathContext
from pyligent.core.solvers.llm import DiligentTokensConfig


def generate_one_action_guided(
    *,
    guidance_lm,
    prompt: str,
    tokens_cfg: DiligentTokensConfig,
    max_new_tokens: int,
) -> str:
    """
    Generate exactly one action using guidance with constrained grammar.

    Args:
        guidance_lm: Cached guidance model wrapper
        prompt: Complete formatted prompt
        tokens_cfg: Token configuration (controls which tags are available)
        max_new_tokens: Maximum tokens to generate

    Returns:
        Complete action string: "<tag>content</tag>"
    """
    node_s, node_e = tokens_cfg.node_start, tokens_cfg.node_end
    done_s, done_e = tokens_cfg.done_start, tokens_cfg.done_end

    # Get valid tag options based on configuration
    valid_tags = tokens_cfg.get_inference_tags()

    # Start generation from prompt
    lm = guidance_lm + prompt

    # Constrained grammar: select tag -> generate content -> close tag
    tag = guidance.select(valid_tags, name="tag_start")
    lm += tag

    if lm["tag_start"] == node_s:
        # Node: ID + reasoning text
        lm += guidance.gen(max_tokens=max_new_tokens, stop=node_e, name="content")
        lm += node_e
        end_tag = node_e
    elif lm["tag_start"] == done_s:
        # Done: final answer
        lm += guidance.gen(max_tokens=max_new_tokens, stop=done_e, name="content")
        lm += done_e
        end_tag = done_e
    else:
        # Backtrack: just ID (short)
        _bt_s, bt_e = tokens_cfg.backtrack_start, tokens_cfg.backtrack_end
        lm += guidance.gen(max_tokens=20, stop=bt_e, name="content")
        lm += bt_e
        end_tag = bt_e

    # Reconstruct complete action string
    return f"{lm['tag_start']}{lm['content']}{end_tag}"


def generate_k_actions_guided(
    *,
    guidance_lm,
    prompt: str,
    tokens_cfg: DiligentTokensConfig,
    max_new_tokens: int,
    K: int,
) -> List[str]:
    """
    Generate K diverse action sequences using guidance.

    Args:
        guidance_lm: Cached guidance model wrapper
        prompt: Complete formatted prompt
        tokens_cfg: Token configuration
        max_new_tokens: Maximum tokens per generation
        K: Number of sequences to generate

    Returns:
        List of K action strings
    """
    actions = []

    for _ in range(K):
        try:
            action_str = generate_one_action_guided(
                guidance_lm=guidance_lm,
                prompt=prompt,
                tokens_cfg=tokens_cfg,
                max_new_tokens=max_new_tokens,
            )
            actions.append(action_str)
        except Exception as e:
            logger.warning(f"Guidance generation failed for sequence: {e}")
            # Add empty or error placeholder
            actions.append("<error>generation failed</error>")

    return actions


def generate_actions_guided_batch(
    *,
    guidance_lm,
    contexts: List[PathContext],
    prompt_builder: Callable[[PathContext], str],
    tokens_cfg: DiligentTokensConfig,
    max_new_tokens: int,
    K: int = 1,
) -> Tuple[List[List[str]], int]:
    """
    Generate K actions for each context using guidance.

    This is the main entry point that matches the solver's propose_actions signature.

    Args:
        guidance_lm: Cached guidance model wrapper
        contexts: List of PathContext objects
        prompt_builder: Function to build prompt from PathContext
        tokens_cfg: Token configuration
        max_new_tokens: Maximum tokens per generation
        K: Number of sequences per context

    Returns:
        (batched_actions, solver_calls)
            - batched_actions: [[K actions for ctx1], [K actions for ctx2], ...]
            - solver_calls: total number of forward passes
    """
    batched_actions = []
    solver_calls = 0

    for ctx in contexts:
        prompt = prompt_builder(ctx)

        if K == 1:
            # Single action per context
            action_str = generate_one_action_guided(
                guidance_lm=guidance_lm,
                prompt=prompt,
                tokens_cfg=tokens_cfg,
                max_new_tokens=max_new_tokens,
            )
            batched_actions.append([action_str])
            solver_calls += 1
        else:
            # K actions per context
            actions = generate_k_actions_guided(
                guidance_lm=guidance_lm,
                prompt=prompt,
                tokens_cfg=tokens_cfg,
                max_new_tokens=max_new_tokens,
                K=K,
            )
            batched_actions.append(actions)
            solver_calls += K

    return batched_actions, solver_calls
