"""Static HTML review page and picks YAML for annotate export/import.

Injection boundary: copy plan strings into escaped HTML only. Do not search
ReasonHub. Import never writes bindings.yaml.
"""

from __future__ import annotations

import html
from pathlib import Path

import click
from ruamel.yaml import YAML

REVIEW_NAME = "annotate-review.html"
ACCEPT = "accept"
REJECT = "reject"
REPLACE = "replace"
UNBOUND = "unbound"
PENDING = "pending"
SKIP = "skip"
VALID_DECISIONS = {ACCEPT, REJECT, REPLACE, UNBOUND, PENDING, SKIP}


def _yaml() -> YAML:
    y = YAML()
    y.default_flow_style = False
    y.preserve_quotes = True
    return y


def load_picks(path: Path) -> dict:
    if not path.is_file():
        raise click.ClickException(f"Picks file not found: {path}")
    with open(path, encoding="utf-8") as f:
        data = _yaml().load(f) or {}
    if not isinstance(data, dict):
        raise click.ClickException(f"Picks file must be a YAML mapping: {path}")
    return data


def _esc(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def _candidate_for_pick(element: dict, pick: int) -> dict | None:
    candidates = list(element.get("candidates") or [])
    for cand in candidates:
        try:
            rank = int(cand.get("rank"))
        except (TypeError, ValueError):
            continue
        if rank == pick:
            return cand
    if 1 <= pick <= len(candidates):
        return candidates[pick - 1]
    return None


def _chosen_from_candidate(cand: dict) -> dict:
    return {
        "system": cand.get("system"),
        "code": cand.get("code"),
        "display": cand.get("display"),
    }


def _empty_chosen() -> dict:
    return {"system": None, "code": None, "display": None}


def _pick_int(raw) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise click.ClickException(f"Invalid pick {raw!r}; expected a 1-based rank") from exc


def apply_picks(plan: dict, picks: dict, model: str) -> None:
    """Mutate plan from picks. Raise before mutating if any row is invalid."""
    picks_model = picks.get("model")
    if picks_model is not None and str(picks_model) != str(model):
        raise click.ClickException(
            f"Picks model {picks_model!r} does not match {model!r}."
        )
    rows = picks.get("picks")
    if rows is None:
        raise click.ClickException("Picks file has no 'picks' list.")
    if not isinstance(rows, list):
        raise click.ClickException("Picks 'picks' must be a list.")

    by_path = {el.get("path"): el for el in plan.get("elements") or [] if el.get("path")}
    validated: list[tuple[dict, dict]] = []
    for i, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise click.ClickException(f"Picks row {i} must be a mapping.")
        path = row.get("path")
        if not path:
            raise click.ClickException(f"Picks row {i} has no path.")
        element = by_path.get(path)
        if element is None:
            raise click.ClickException(
                f"Path {path!r} is not in the annotate plan. Import does not add elements."
            )
        decision = (row.get("decision") or PENDING).strip()
        if decision not in VALID_DECISIONS:
            raise click.ClickException(f"Unknown decision {decision!r} for {path}.")
        if decision == SKIP:
            decision = REJECT
        pick = _pick_int(row.get("pick"))
        reason = row.get("reason") or ""
        chosen_in = row.get("chosen") or {}
        if decision == ACCEPT:
            if pick is None:
                raise click.ClickException(f"Path {path} is accept but pick rank is missing.")
            cand = _candidate_for_pick(element, pick)
            if cand is None:
                raise click.ClickException(
                    f"Path {path} pick {pick} is not a candidate on the plan."
                )
            validated.append(
                (
                    element,
                    {
                        "decision": ACCEPT,
                        "pick_chosen": _chosen_from_candidate(cand),
                        "reason": reason,
                    },
                )
            )
        elif decision == UNBOUND:
            if not str(reason).strip():
                raise click.ClickException(f"Path {path} is unbound but has no reason.")
            validated.append((element, {"decision": UNBOUND, "reason": str(reason).strip()}))
        elif decision == REPLACE:
            system = (chosen_in.get("system") if isinstance(chosen_in, dict) else None) or None
            code = (chosen_in.get("code") if isinstance(chosen_in, dict) else None) or None
            display = (chosen_in.get("display") if isinstance(chosen_in, dict) else None) or ""
            if not system or not code:
                raise click.ClickException(
                    f"Path {path} is replace but chosen system/code is missing."
                )
            validated.append(
                (
                    element,
                    {
                        "decision": REPLACE,
                        "pick_chosen": {"system": system, "code": code, "display": display},
                        "reason": reason or "",
                    },
                )
            )
        else:
            validated.append((element, {"decision": decision, "reason": reason or ""}))

    for element, patch in validated:
        element["decision"] = patch["decision"]
        if "reason" in patch:
            element["reason"] = patch["reason"]
        if patch["decision"] == ACCEPT:
            element["chosen"] = patch["pick_chosen"]
        elif patch["decision"] == REPLACE:
            element["chosen"] = patch["pick_chosen"]
        elif patch["decision"] == UNBOUND:
            element["chosen"] = _empty_chosen()
    plan["status"] = "draft"


def _selected_accept_rank(element: dict) -> int | None:
    if (element.get("decision") or "") != ACCEPT:
        return None
    chosen = element.get("chosen") or {}
    system = chosen.get("system")
    code = None if chosen.get("code") is None else str(chosen.get("code"))
    if not system or not code:
        return None
    for i, cand in enumerate(element.get("candidates") or [], start=1):
        cand_code = None if cand.get("code") is None else str(cand.get("code"))
        if cand.get("system") == system and cand_code == code:
            try:
                return int(cand.get("rank") or i)
            except (TypeError, ValueError):
                return i
    return None


def _radio(name: str, value: str, label: str, checked: bool) -> str:
    chk = " checked" if checked else ""
    return (
        f'<label><input type="radio" name="{_esc(name)}" value="{_esc(value)}"{chk}/> '
        f"{label}</label>"
    )


def _render_element(index: int, element: dict) -> str:
    path = element.get("path") or ""
    display = element.get("display") or ""
    query = element.get("query") or ""
    decision = element.get("decision") or PENDING
    reason = element.get("reason") or ""
    name = f"choice-{index}"
    accept_rank = _selected_accept_rank(element)
    skip_checked = decision in (PENDING, REJECT)
    if decision in (ACCEPT, UNBOUND, REPLACE):
        skip_checked = False

    options = [
        _radio(name, "skip", "Skip (leave undecided this round)", skip_checked),
        _radio(name, "unbound", "Unbound (no code; reason required)", decision == UNBOUND),
        _radio(name, "replace", "Replace (enter system / code / display)", decision == REPLACE),
    ]
    for i, cand in enumerate(element.get("candidates") or [], start=1):
        try:
            rank = int(cand.get("rank") or i)
        except (TypeError, ValueError):
            rank = i
        code = cand.get("code")
        disp = cand.get("display") or ""
        sys = cand.get("system") or ""
        label = (
            f"Rank {rank}: {_esc(disp)} "
            f"(<code>{_esc(code)}</code> · {_esc(sys)})"
        )
        options.append(_radio(name, str(rank), label, accept_rank == rank))

    chosen = element.get("chosen") or {}
    replace = (
        '<div class="replace-fields">'
        f'<label>System <input class="replace-system" value="{_esc(chosen.get("system"))}"/></label>'
        f'<label>Code <input class="replace-code" value="{_esc(chosen.get("code"))}"/></label>'
        f'<label>Display <input class="replace-display" value="{_esc(chosen.get("display"))}"/></label>'
        "</div>"
    )
    radios = "\n      ".join(options)
    return f"""  <fieldset class="element" data-path="{_esc(path)}">
    <legend>{_esc(path)}</legend>
    <p class="meta">id={_esc(element.get("id"))} · display={_esc(display)} · query={_esc(query)}</p>
    {radios}
    {replace}
    <label>Reason (required for unbound)<textarea class="reason">{html.escape(str(reason))}</textarea></label>
  </fieldset>"""


DOWNLOAD_JS = r"""
document.getElementById("download").addEventListener("click", function () {
  var model = document.body.getAttribute("data-model") || "";
  var blocks = document.querySelectorAll("fieldset.element");
  var lines = ["model: " + JSON.stringify(model), "picks:"];
  if (!blocks.length) {
    lines.push("  []");
  }
  blocks.forEach(function (fs) {
    var path = fs.getAttribute("data-path") || "";
    var picked = fs.querySelector("input[type=radio]:checked");
    var reason = (fs.querySelector("textarea.reason") || {}).value || "";
    var decision = "pending";
    var pick = "null";
    var sys = "null";
    var code = "null";
    var disp = "null";
    if (picked) {
      var v = picked.value;
      if (v === "skip") {
        decision = "reject";
      } else if (v === "unbound") {
        decision = "unbound";
      } else if (v === "replace") {
        decision = "replace";
        sys = JSON.stringify((fs.querySelector(".replace-system") || {}).value || "");
        code = JSON.stringify((fs.querySelector(".replace-code") || {}).value || "");
        disp = JSON.stringify((fs.querySelector(".replace-display") || {}).value || "");
      } else {
        decision = "accept";
        pick = String(parseInt(v, 10));
      }
    }
    lines.push("  - path: " + JSON.stringify(path));
    lines.push("    decision: " + decision);
    lines.push("    pick: " + pick);
    lines.push("    reason: " + JSON.stringify(reason));
    lines.push("    chosen:");
    lines.push("      system: " + sys);
    lines.push("      code: " + code);
    lines.push("      display: " + disp);
  });
  var blob = new Blob([lines.join("\n") + "\n"], {type: "text/yaml"});
  var a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "annotate-picks.yaml";
  a.click();
  URL.revokeObjectURL(a.href);
});
""".strip()


def render_review_html(plan: dict) -> str:
    model = _esc(plan.get("model") or "")
    elements = list(plan.get("elements") or [])
    blocks = [_render_element(i, el) for i, el in enumerate(elements)]
    body = "\n".join(blocks) or "<p>No planned elements.</p>"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Annotate review — {model}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 1.5rem; max-width: 52rem; }}
    fieldset {{ margin: 0 0 1.25rem; padding: 0.75rem 1rem; }}
    legend {{ font-weight: 600; }}
    .meta {{ color: #444; font-size: 0.9rem; margin: 0.25rem 0 0.75rem; }}
    label {{ display: block; margin: 0.2rem 0; }}
    .replace-fields {{ margin: 0.5rem 0 0.5rem 1.5rem; }}
    textarea {{ width: 100%; min-height: 3rem; }}
    button {{ margin-top: 1rem; padding: 0.4rem 0.8rem; }}
  </style>
</head>
<body data-model="{model}">
  <h1>Annotate review</h1>
  <p>Model <code>{model}</code>. Pick one candidate per element, or unbound / skip / replace.
  Download picks YAML and run <code>rh-mod-skills annotate import</code>. This page does not write bindings.</p>
  {body}
  <button type="button" id="download">Download annotate-picks.yaml</button>
  <script>
{DOWNLOAD_JS}
  </script>
</body>
</html>
"""
