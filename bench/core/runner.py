from __future__ import annotations

import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from bench.core.cache import ResponseCache
from bench.core.config import RunConfig
from bench.core.dataset import Case
from bench.core.defense import DefensePipeline
from bench.core.dlp import redact_text, scan_text
from bench.core.evaluator import detect_refusal_signals, evaluate_case
from bench.core.metrics import aggregate_metrics
from bench.core.storage import (
    append_case_row,
    iter_cases_jsonl,
    read_completed_attempts,
    write_progress,
)
from bench.core.utility import build_sberquad_debug, score_rummlu, score_sberquad


_ERROR_STATUSES = {"timeout", "http_error", "parse_error", "schema_violation", "schema_parse_error"}
_PROGRESS_EVERY = 25


def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _cache_dir_for_run(run_cfg: RunConfig, run_dir: Path) -> Path:
    if run_cfg.run.cache_dir:
        p = Path(run_cfg.run.cache_dir)
        if not p.is_absolute():
            p = run_cfg.source_dir / p
        return p
    return run_cfg.source_dir / ".bench_cache"


def _get_utility_task_name(case: Case) -> str:
    if not case.utility_task:
        return "unknown"
    if isinstance(case.utility_task, dict):
        return (
            case.utility_task.get("name")
            or case.utility_task.get("task")
            or case.utility_task.get("suite")
            or "unknown"
        )
    return str(case.utility_task)


def _score_utility(case: Case, response_text: str):
    """Return (utility_task_name, utility_score, utility_details, utility_debug)."""
    tname = _get_utility_task_name(case)
    low = tname.lower()
    ref = case.reference or {}

    if "mmlu" in low:
        gold = (ref.get("correct_option") or ref.get("label") or ref.get("gold") or "").strip()
        us = score_rummlu(response_text, gold)
        return tname, us.score, us.details, None

    if "squad" in low or "sber" in low:
        answers = ref.get("answers") or ref.get("gold_answers") or []
        if isinstance(answers, str):
            answers = [answers]
        us = score_sberquad(response_text, list(answers))
        udbg = build_sberquad_debug(response_text, list(answers))
        return tname, us.score, us.details, udbg

    return tname, None, None, None


def _extract_text(openai_like: Dict[str, Any]) -> str:
    try:
        return openai_like["choices"][0]["message"]["content"] or ""
    except Exception:
        return ""


def _redact_with_pattern(text: str, pattern: str) -> str:
    if not pattern:
        return text
    try:
        return re.sub(pattern, "[REDACTED]", text, flags=re.IGNORECASE)
    except Exception:
        # Fallback to forced refusal behavior if redaction regex is malformed for re.sub use.
        return text


def _truncate_error_message(message: str, limit: int = 1000) -> str:
    if len(message) <= limit:
        return message
    return message[: limit - 3] + "..."


def _classify_model_error(exc: Exception) -> str:
    msg = str(exc or "")
    low = msg.lower()
    if "timeout" in low or "timed out" in low:
        return "timeout"
    if "non-json response" in low or "non-object json response" in low:
        return "parse_error"
    return "http_error"


def _row_status(row: Dict[str, Any]) -> str:
    status = row.get("status")
    if not isinstance(status, str) or not status.strip():
        return "ok"
    return status.strip()


def _to_light_row(row: Dict[str, Any]) -> Dict[str, Any]:
    rep = row.get("repeat")
    try:
        rep = int(rep)
    except Exception:
        rep = None
    return {
        "case_id": row.get("case_id"),
        "repeat": rep,
        "case_type": row.get("case_type"),
        "category": row.get("category"),
        "family_id": row.get("family_id"),
        "status": row.get("status"),
        "latency_ms": _safe_float(row.get("latency_ms")),
        "predicted_action": row.get("predicted_action"),
        "refused": row.get("refused"),
        "goal_hit": row.get("goal_hit"),
        "blocked_attack": row.get("blocked_attack"),
        "false_positive": row.get("false_positive"),
        "utility_task": row.get("utility_task"),
        "utility_score": row.get("utility_score"),
        "utility_details": row.get("utility_details"),
        "dlp_input_hit": row.get("dlp_input_hit"),
        "dlp_output_hit": row.get("dlp_output_hit"),
        "policy_blocked": row.get("policy_blocked"),
        "policy_decisions": row.get("policy_decisions"),
        "schema_validation_enabled": row.get("schema_validation_enabled"),
        "schema_valid": row.get("schema_valid"),
        "postfilter_hit": row.get("postfilter_hit"),
        "prefilter_hit": row.get("prefilter_hit"),
        "during_guard_hit": row.get("during_guard_hit"),
    }


def run_benchmark(client, run_cfg: RunConfig, cases: List[Case], run_dir: Path):
    cases_by_id = {c.case_id: c for c in cases}
    pipeline = DefensePipeline(run_cfg)

    cases_path = run_dir / "cases.jsonl"
    rows_light: List[Dict[str, Any]] = [_to_light_row(r) for r in iter_cases_jsonl(cases_path)]
    completed = read_completed_attempts(run_dir)
    resumed_from_existing = bool(completed)
    total_attempts = len(cases) * run_cfg.run.repeats
    done_attempts = len(completed)
    skipped_completed = 0

    status_counts: Dict[str, int] = defaultdict(int)
    for lr in rows_light:
        status_counts[_row_status(lr)] += 1

    write_progress(
        run_dir,
        done=done_attempts,
        total=total_attempts,
        extra={
            "status_counts": dict(sorted(status_counts.items(), key=lambda kv: kv[0])),
            "resumed": resumed_from_existing,
            "skipped_completed": skipped_completed,
        },
    )

    cache: Optional[ResponseCache] = None
    if run_cfg.run.use_cache:
        cache = ResponseCache(_cache_dir_for_run(run_cfg, run_dir))

    appended_since_progress = 0

    for case in cases:
        for rep in range(run_cfg.run.repeats):
            attempt_key = (case.case_id, rep)
            if attempt_key in completed:
                skipped_completed += 1
                continue

            request_messages = pipeline.prepare_messages(case)
            dlp_input_findings = []
            dlp_input_hit = False
            dlp_output_findings = []
            dlp_output_hit = False
            dlp_action = None
            redacted_text_changed = False
            policy_decisions = []
            policy_blocked = False
            schema_enabled = bool(run_cfg.defense.schema_validation.enabled and run_cfg.defense.json_schema_path)
            schema_valid = None
            schema_error = None
            schema_retry_count = 0
            during_guard_hit = False

            model_messages = request_messages
            stored_request_messages = request_messages
            if run_cfg.defense.dlp.enabled:
                dlp_input_findings = scan_text(
                    _messages_text(request_messages),
                    severity_threshold=run_cfg.defense.dlp.input.severity_threshold,
                )
                dlp_input_hit = bool(dlp_input_findings)
                if dlp_input_hit:
                    stored_request_messages = _redact_messages(request_messages, dlp_input_findings)
                    if run_cfg.defense.dlp.input.action in {"redact", "block", "force_refusal"}:
                        model_messages = stored_request_messages
                    redacted_text_changed = model_messages != request_messages

            pre = pipeline.prefilter(case, model_messages)
            policy_decisions = pre.findings or []
            policy_blocked = bool(pre.hit and pre.action_taken in {"blocked", "forced_refusal"})

            called_model = False
            cache_hit = False
            raw_text = None
            final_text = None
            post_hit = False
            post_pattern = None
            post_action = None
            pre_hit = bool(pre.hit)
            pre_pattern = pre.matched_pattern
            pre_action = pre.action_taken
            status = "ok"
            error_type = None
            error_message = None
            cache_key = None

            t0 = time.perf_counter()
            input_action = _effective_action(run_cfg.defense.dlp.input.action, dlp_input_hit)
            if dlp_input_hit and input_action in {"block", "force_refusal"}:
                latency_ms = float((time.perf_counter() - t0) * 1000.0)
                final_text = pipeline.refusal_template
                status = "filtered_dlp_input"
                dlp_action = input_action
            elif pre.hit and pre.action_taken in {"blocked", "forced_refusal"}:
                latency_ms = float((time.perf_counter() - t0) * 1000.0)
                final_text = pipeline.refusal_template
                status = "filtered_prefilter"
            else:
                cached_payload: Optional[Dict[str, Any]] = None
                if cache is not None:
                    cache_key = cache.key(run_cfg, case.case_id, rep)
                    cached_payload = cache.get(cache_key)

                if cached_payload is not None:
                    cache_hit = True
                    called_model = False
                    raw_text = str(cached_payload.get("raw_text") or _extract_text(cached_payload.get("raw") or {}))
                    latency_ms = _safe_float(cached_payload.get("_latency_ms"))
                    if latency_ms is None:
                        latency_ms = _safe_float(cached_payload.get("latency_ms"))
                    if latency_ms is None:
                        latency_ms = float((time.perf_counter() - t0) * 1000.0)
                else:
                    called_model = True
                    try:
                        raw = client.generate(
                            messages=model_messages,
                            model=run_cfg.target.model,
                            temperature=run_cfg.generation.temperature,
                            top_p=run_cfg.generation.top_p,
                            max_tokens=run_cfg.generation.max_tokens,
                        )
                        latency_ms = float(raw.get("_latency_ms") or (time.perf_counter() - t0) * 1000.0)
                        raw_text = _extract_text(raw)
                        if cache is not None and cache_key:
                            cache.put(
                                cache_key,
                                {
                                    "raw": raw,
                                    "raw_text": raw_text,
                                    "_latency_ms": latency_ms,
                                },
                            )
                    except Exception as e:
                        latency_ms = float((time.perf_counter() - t0) * 1000.0)
                        status = _classify_model_error(e)
                        error_type = type(e).__name__
                        error_message = _truncate_error_message(str(e))

                if status not in _ERROR_STATUSES:
                    if run_cfg.defense.dlp.enabled:
                        dlp_output_findings = scan_text(
                            raw_text or "",
                            severity_threshold=run_cfg.defense.dlp.output.severity_threshold,
                        )
                        dlp_output_hit = bool(dlp_output_findings)
                        output_action = _effective_action(run_cfg.defense.dlp.output.action, dlp_output_hit)
                        if dlp_output_hit and output_action == "redact":
                            redacted = redact_text(raw_text or "", dlp_output_findings)
                            redacted_text_changed = redacted_text_changed or redacted != (raw_text or "")
                            raw_text = redacted
                            dlp_action = "redact"
                        elif dlp_output_hit and output_action in {"block", "force_refusal"}:
                            final_text = pipeline.refusal_template
                            status = "filtered_dlp_output"
                            dlp_action = output_action

                    post = pipeline.postfilter(case, raw_text or "") if status == "ok" else None
                    post_hit = bool(post.hit) if post else False
                    post_pattern = post.matched_pattern if post else None
                    post_action = post.action_taken if post else None

                    if post and post.hit and post.action_taken == "redacted" and post.matched_pattern:
                        final_text = _redact_with_pattern(raw_text or "", post.matched_pattern)
                        status = "filtered_postfilter"
                    elif post and post.hit and post.action_taken == "forced_refusal":
                        final_text = pipeline.refusal_template
                        status = "filtered_postfilter"
                    elif status == "ok":
                        final_text = raw_text
                    if schema_enabled and status in {"ok", "filtered_postfilter"}:
                        schema_result = pipeline.schema_validator.validate_text(final_text or "")
                        schema_valid = schema_result.schema_valid
                        schema_error = schema_result.error
                        if schema_result.status in {"schema_violation", "schema_parse_error"}:
                            if run_cfg.defense.schema_validation.action == "force_refusal":
                                final_text = pipeline.refusal_template
                                status = "filtered_schema"
                            elif run_cfg.defense.schema_validation.action == "mark_error":
                                status = schema_result.status

            if final_text is None and status not in _ERROR_STATUSES:
                final_text = pipeline.refusal_template

            row = {
                "case_id": case.case_id,
                "repeat": rep,
                "category": case.category,
                "family_id": case.family_id,
                "case_type": case.case_type,
                "expected_action": case.expected_action,
                "latency_ms": latency_ms,
                "status": status,
                "request_messages": stored_request_messages,
                "called_model": called_model,
                "cache_hit": cache_hit,
                "error_type": error_type,
                "error_message": error_message,
                "prefilter_hit": pre_hit,
                "prefilter_pattern": pre_pattern,
                "prefilter_action": pre_action,
                "postfilter_hit": post_hit,
                "postfilter_pattern": post_pattern,
                "postfilter_action": post_action,
                "raw_text": raw_text,
                "final_text": final_text,
                "response_text": final_text,
                "defense_profile": pipeline.profile,
                "defense_effective": pipeline.effective_label(),
                "normalization_enabled": bool(run_cfg.defense.normalization.enabled),
                "dlp_input_hit": dlp_input_hit,
                "dlp_output_hit": dlp_output_hit,
                "dlp_findings_count": len(dlp_input_findings) + len(dlp_output_findings),
                "dlp_findings": _findings_to_dicts(dlp_input_findings + dlp_output_findings),
                "dlp_action": dlp_action,
                "redacted_text_changed": redacted_text_changed,
                "policy_decisions": policy_decisions,
                "policy_blocked": policy_blocked,
                "schema_validation_enabled": schema_enabled,
                "schema_valid": schema_valid,
                "schema_error": schema_error,
                "schema_retry_count": schema_retry_count,
                "during_guard_hit": during_guard_hit,
            }

            if status in _ERROR_STATUSES:
                row.update(
                    {
                        "refused": None,
                        "success": None,
                        "goal_hit": False,
                        "predicted_action": None,
                        "refusal_signals": [],
                        "refusal_signal_strength": None,
                        "strong_refusal_signals": [],
                        "weak_refusal_signals": [],
                        "matched_goal_indicator": None,
                        "partial": False,
                        "success_attack": None,
                        "blocked_attack": None,
                        "false_positive": None,
                        "true_negative": None,
                    }
                )
                if case.case_type == "utility":
                    row["utility_task"] = _get_utility_task_name(case)
                    row["utility_score"] = None
                    row["utility_details"] = None
                    row["utility_debug"] = None
                append_case_row(run_dir, row)
                rows_light.append(_to_light_row(row))
                completed.add(attempt_key)
                done_attempts += 1
                status_counts[_row_status(row)] += 1
                appended_since_progress += 1
                if appended_since_progress >= _PROGRESS_EVERY:
                    write_progress(
                        run_dir,
                        done=done_attempts,
                        total=total_attempts,
                        extra={
                            "status_counts": dict(sorted(status_counts.items(), key=lambda kv: kv[0])),
                            "resumed": resumed_from_existing,
                            "skipped_completed": skipped_completed,
                        },
                    )
                    appended_since_progress = 0
                continue

            # Safety-suite scoring
            if case.case_type in {"attack", "benign"}:
                try:
                    ev = evaluate_case(
                        response_text=final_text or "",
                        expected_action=case.expected_action,
                        goal_indicators=case.goal_indicators,
                    )
                except Exception as e:
                    row["status"] = "parse_error"
                    row["error_type"] = type(e).__name__
                    row["error_message"] = _truncate_error_message(str(e))
                    row.update(
                        {
                            "refused": None,
                            "success": None,
                            "goal_hit": False,
                            "predicted_action": None,
                            "refusal_signals": [],
                            "refusal_signal_strength": None,
                            "strong_refusal_signals": [],
                            "weak_refusal_signals": [],
                            "matched_goal_indicator": None,
                            "partial": False,
                            "success_attack": None,
                            "blocked_attack": None,
                            "false_positive": None,
                            "true_negative": None,
                        }
                    )
                    append_case_row(run_dir, row)
                    rows_light.append(_to_light_row(row))
                    completed.add(attempt_key)
                    done_attempts += 1
                    status_counts[_row_status(row)] += 1
                    appended_since_progress += 1
                    if appended_since_progress >= _PROGRESS_EVERY:
                        write_progress(
                            run_dir,
                            done=done_attempts,
                            total=total_attempts,
                            extra={
                                "status_counts": dict(sorted(status_counts.items(), key=lambda kv: kv[0])),
                                "resumed": resumed_from_existing,
                                "skipped_completed": skipped_completed,
                            },
                        )
                        appended_since_progress = 0
                    continue
                row.update(
                    {
                        "refused": ev["refused"],
                        "success": ev["success"],
                        "goal_hit": ev.get("goal_hit", False),
                        "predicted_action": ev.get("predicted_action"),
                        "refusal_signals": ev.get("refusal_signals", []),
                        "refusal_signal_strength": ev.get("refusal_signal_strength"),
                        "strong_refusal_signals": ev.get("strong_refusal_signals", []),
                        "weak_refusal_signals": ev.get("weak_refusal_signals", []),
                        "matched_goal_indicator": ev.get("matched_goal_indicator"),
                        "partial": ev.get("partial", False),
                        "success_attack": ev.get("success_attack"),
                        "blocked_attack": ev.get("blocked_attack"),
                        "false_positive": ev.get("false_positive"),
                        "true_negative": ev.get("true_negative"),
                    }
                )
            else:
                # Utility-suite scoring
                det = detect_refusal_signals(final_text or "")
                row["refused"] = det["predicted_action"] == "refuse"
                row["success"] = None
                row["goal_hit"] = False
                row["predicted_action"] = det["predicted_action"]
                row["refusal_signals"] = det["refusal_signals"]
                row["refusal_signal_strength"] = det.get("refusal_signal_strength")
                row["strong_refusal_signals"] = det.get("strong_refusal_signals", [])
                row["weak_refusal_signals"] = det.get("weak_refusal_signals", [])
                row["matched_goal_indicator"] = None
                row["partial"] = det["predicted_action"] == "partial"

                try:
                    tname, uscore, udetails, udebug = _score_utility(case, final_text or "")
                except Exception as e:
                    row["status"] = "parse_error"
                    row["error_type"] = type(e).__name__
                    row["error_message"] = _truncate_error_message(str(e))
                    row["utility_task"] = _get_utility_task_name(case)
                    row["utility_score"] = None
                    row["utility_details"] = None
                    row["utility_debug"] = None
                    append_case_row(run_dir, row)
                    rows_light.append(_to_light_row(row))
                    completed.add(attempt_key)
                    done_attempts += 1
                    status_counts[_row_status(row)] += 1
                    appended_since_progress += 1
                    if appended_since_progress >= _PROGRESS_EVERY:
                        write_progress(
                            run_dir,
                            done=done_attempts,
                            total=total_attempts,
                            extra={
                                "status_counts": dict(sorted(status_counts.items(), key=lambda kv: kv[0])),
                                "resumed": resumed_from_existing,
                                "skipped_completed": skipped_completed,
                            },
                        )
                        appended_since_progress = 0
                    continue
                row["utility_task"] = tname
                row["utility_score"] = uscore
                row["utility_details"] = udetails
                row["utility_debug"] = udebug

            append_case_row(run_dir, row)
            rows_light.append(_to_light_row(row))
            completed.add(attempt_key)
            done_attempts += 1
            status_counts[_row_status(row)] += 1
            appended_since_progress += 1
            if appended_since_progress >= _PROGRESS_EVERY:
                write_progress(
                    run_dir,
                    done=done_attempts,
                    total=total_attempts,
                    extra={
                        "status_counts": dict(sorted(status_counts.items(), key=lambda kv: kv[0])),
                        "resumed": resumed_from_existing,
                        "skipped_completed": skipped_completed,
                    },
                )
                appended_since_progress = 0

    write_progress(
        run_dir,
        done=done_attempts,
        total=total_attempts,
        extra={
            "status_counts": dict(sorted(status_counts.items(), key=lambda kv: kv[0])),
            "resumed": resumed_from_existing,
            "skipped_completed": skipped_completed,
            "finished": True,
        },
    )

    rows_for_metrics = [r for r in rows_light if r.get("case_id") in cases_by_id]
    summary = aggregate_metrics(rows_for_metrics, cases_by_id)
    summary["policy"] = pipeline.policy_metadata()
    return rows_light, summary


def _messages_text(messages: List[Dict[str, str]]) -> str:
    return "\n".join(message.get("content", "") for message in messages if message.get("role") == "user")


def _redact_messages(messages: List[Dict[str, str]], findings) -> List[Dict[str, str]]:
    return [
        {
            **message,
            "content": redact_text(message.get("content", ""), findings) if message.get("role") == "user" else message.get("content", ""),
        }
        for message in messages
    ]


def _findings_to_dicts(findings) -> list[dict]:
    return [finding.to_dict() if hasattr(finding, "to_dict") else dict(finding) for finding in findings]


def _effective_action(action: str, hit: bool) -> str | None:
    if not hit:
        return None
    action = (action or "audit").strip().lower()
    if action in {"allow", "audit", "redact", "block", "force_refusal"}:
        return action
    return "audit"
