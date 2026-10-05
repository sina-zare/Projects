#!/usr/bin/env python3
"""
Generate a Mermaid flowchart (and a Markdown recipient table) from enabled
Zabbix trigger actions.

Default view:
    action block (name + bulleted conditions) --> endpoint (media + recipients)

--by-recipient view (hybrid):
    action --(media)--> recipient hub     for recipients used by >= N actions
    action --> endpoint block             for everyone else (one block per action/media)

Usage:
    export ZABBIX_TOKEN=...
    python3 zabbix_actions_mermaid.py --by-recipient --per-row 4 --width 420 --merge --elk
    python3 zabbix_actions_mermaid.py --dir LR
"""

import argparse
import os
import re
from collections import defaultdict

from pyzabbix import ZabbixAPI

CONDITION_TYPES = {
    "0": "Host group",
    "1": "Host",
    "2": "Trigger",
    "3": "Event name",
    "4": "Trigger severity",
    "6": "Time period",
    "13": "Host template",
    "16": "Problem suppressed",
    "25": "Event tag",
    "26": "Event tag value",
}

OPERATORS = {
    "0": "equals",
    "1": "does not equal",
    "2": "contains",
    "3": "does not contain",
    "4": "in",
    "5": "is greater than or equals",
    "6": "is less than or equals",
    "7": "not in",
    "8": "matches",
    "9": "does not match",
    "10": "Yes",
    "11": "No",
}

SEVERITIES = {
    "0": "Not classified",
    "1": "Information",
    "2": "Warning",
    "3": "Average",
    "4": "High",
    "5": "Disaster",
}

EVALTYPES = {"0": "And/Or", "1": "And", "2": "Or"}

BULLET = "•"
DIVIDER = "─" * 12

# Media type colours: (fill, stroke, text). Matched by keyword in the media name.
MEDIA_COLORS = [
    ("mattermost",      ("#dbeafe", "#2563eb", "#1e3a8a")),
    ("sms",        ("#ffedd5", "#ea580c", "#7c2d12")),
    ("email", ("#dcfce7", "#16a34a", "#14532d")),
    ("all media",  ("#e5e7eb", "#6b7280", "#111827")),
]
FALLBACK_COLORS = [
    ("#fae8ff", "#c026d3", "#701a75"),
    ("#fef9c3", "#ca8a04", "#713f12"),
    ("#cffafe", "#0891b2", "#164e63"),
    ("#fee2e2", "#dc2626", "#7f1d1d"),
]

# Single quotes inside the style attribute: the label itself is double-quoted.
LEFT_OPEN = "<div style='text-align:left'>"
LEFT_CLOSE = "</div>"


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def escape(text):
    """Escape text for Mermaid labels (Mermaid's #entity; syntax)."""
    return (
        str(text)
        .replace("#", "#35;")   # must be first
        .replace("&", "#amp;")
        .replace('"', "#quot;")
        .replace("<", "#lt;")
        .replace(">", "#gt;")
    )


def md_escape(text):
    return str(text).replace("|", "\\|")


# --------------------------------------------------------------------------
# Zabbix API
# --------------------------------------------------------------------------

def get_actions(zapi):
    return zapi.action.get(
        output=["actionid", "name", "status", "eventsource"],
        filter={"eventsource": 0, "status": 0},  # enabled trigger actions
        selectFilter="extend",
        selectOperations="extend",
        sortfield="name",
    )


def build_lookup_tables(zapi, actions):
    """Resolve IDs used by conditions/operations into human-readable names."""
    ids = {k: set() for k in
           ("hostgroups", "hosts", "triggers", "templates",
            "users", "usergroups", "mediatypes")}

    cond_map = {"0": "hostgroups", "1": "hosts", "2": "triggers", "13": "templates"}

    for action in actions:
        for c in action.get("filter", {}).get("conditions", []):
            key = cond_map.get(str(c["conditiontype"]))
            if key:
                ids[key].add(str(c.get("value", "")))

        for op in action.get("operations", []):
            for u in op.get("opmessage_usr", []):
                ids["users"].add(str(u["userid"]))
            for g in op.get("opmessage_grp", []):
                ids["usergroups"].add(str(g["usrgrpid"]))
            mt = str(op.get("opmessage", {}).get("mediatypeid", "0"))
            if mt != "0":
                ids["mediatypes"].add(mt)

    lookups = {k: {} for k in ids}

    if ids["hostgroups"]:
        r = zapi.hostgroup.get(groupids=list(ids["hostgroups"]), output=["groupid", "name"])
        lookups["hostgroups"] = {x["groupid"]: x["name"] for x in r}

    if ids["hosts"]:
        r = zapi.host.get(hostids=list(ids["hosts"]), output=["hostid", "name"])
        lookups["hosts"] = {x["hostid"]: x["name"] for x in r}

    if ids["triggers"]:
        r = zapi.trigger.get(triggerids=list(ids["triggers"]), output=["triggerid", "description"])
        lookups["triggers"] = {x["triggerid"]: x["description"] for x in r}

    if ids["templates"]:
        r = zapi.template.get(templateids=list(ids["templates"]), output=["templateid", "name"])
        lookups["templates"] = {x["templateid"]: x["name"] for x in r}

    if ids["users"]:
        r = zapi.user.get(userids=list(ids["users"]),
                          output=["userid", "username", "name", "surname"])
        for x in r:
            full = f'{x.get("name", "")} {x.get("surname", "")}'.strip()
            lookups["users"][x["userid"]] = x["username"] + (f" ({full})" if full else "")

    if ids["usergroups"]:
        r = zapi.usergroup.get(usrgrpids=list(ids["usergroups"]), output=["usrgrpid", "name"])
        lookups["usergroups"] = {x["usrgrpid"]: x["name"] for x in r}

    if ids["mediatypes"]:
        r = zapi.mediatype.get(mediatypeids=list(ids["mediatypes"]), output=["mediatypeid", "name"])
        lookups["mediatypes"] = {x["mediatypeid"]: x["name"] for x in r}

    return lookups


# --------------------------------------------------------------------------
# Conditions
# --------------------------------------------------------------------------

def resolve_parts(condition, lookups):
    """Return (field name, operator text, resolved value) for one condition."""
    ctype = str(condition["conditiontype"])
    op = OPERATORS.get(str(condition["operator"]), f'operator {condition["operator"]}')
    value = str(condition.get("value", ""))

    if ctype == "0":
        value = lookups["hostgroups"].get(value, value)
    elif ctype == "1":
        value = lookups["hosts"].get(value, value)
    elif ctype == "2":
        value = lookups["triggers"].get(value, value)
    elif ctype == "13":
        value = lookups["templates"].get(value, value)
    elif ctype == "4":
        value = SEVERITIES.get(value, value)

    name = CONDITION_TYPES.get(ctype, f"Condition {ctype}")
    if ctype == "26":
        name = f'Event tag {condition.get("value2", "")}'
    return name, op, value


def format_conditions(conditions, lookups, evaltype, merge=False):
    """
    Return bullet lines (already escaped, HTML-ready).
    Default: one bullet per condition.
    merge=True: same field + operator share one bullet ("A · B").
    Custom-formula actions always get one bullet per condition, prefixed with
    their formula id ([A], [B], ...), so the formula stays readable.
    """
    if evaltype == "3":
        out = []
        for c in conditions:
            name, op, value = resolve_parts(c, lookups)
            out.append(
                f'{BULLET} [{escape(c.get("formulaid", ""))}] '
                f"<b>{escape(name)}</b> {escape(op)} {escape(value)}"
            )
        return out

    if not merge:
        out = []
        for c in conditions:
            name, op, value = resolve_parts(c, lookups)
            out.append(f"{BULLET} <b>{escape(name)}</b> {escape(op)} {escape(value)}")
        return out

    grouped = {}  # (name, op) -> [values]
    for c in conditions:
        name, op, value = resolve_parts(c, lookups)
        grouped.setdefault((name, op), []).append(value)

    out = []
    for (name, op), values in grouped.items():
        if len(values) == 1:
            out.append(f"{BULLET} <b>{escape(name)}</b> {escape(op)} {escape(values[0])}")
        else:
            out.append(
                f"{BULLET} <b>{escape(name)}</b> {escape(op)}: "
                + " · ".join(escape(v) for v in values)
            )
    return out


# --------------------------------------------------------------------------
# Recipients
# --------------------------------------------------------------------------

def action_node_id(action):
    return f'action_{action["actionid"]}'


def collect_sends(actions, lookups):
    """
    action node id -> [(media_name, [(recipient_key, recipient_name), ...]), ...]
    recipient_key is ("user", id) or ("group", id).
    """
    sends = {}
    for action in actions:
        items = []
        for op in action.get("operations", []):
            if str(op.get("operationtype")) != "0":  # 0 = send message
                continue

            mt = str(op.get("opmessage", {}).get("mediatypeid", "0"))
            media = "All media" if mt == "0" else lookups["mediatypes"].get(mt, f"Media {mt}")

            recips = []
            for g in op.get("opmessage_grp", []):
                gid = str(g["usrgrpid"])
                recips.append((("group", gid), "Group: " + lookups["usergroups"].get(gid, gid)))
            for u in op.get("opmessage_usr", []):
                uid = str(u["userid"])
                recips.append((("user", uid), lookups["users"].get(uid, f"User {uid}")))

            items.append((media, recips))
        sends[action_node_id(action)] = items
    return sends


def recipient_stats(actions, sends):
    """recipient_key -> {name, actions: set(action ids), media: {media: set(action ids)}}"""
    stats = {}
    for action in actions:
        aid = action_node_id(action)
        for media, recips in sends[aid]:
            for rkey, rname in recips:
                s = stats.setdefault(
                    rkey, {"name": rname, "actions": set(), "media": defaultdict(set)}
                )
                s["actions"].add(aid)
                s["media"][media].add(aid)
    return stats


# --------------------------------------------------------------------------
# Mermaid
# --------------------------------------------------------------------------

def media_style(media_name, fallback_state):
    """Return (css_class, (fill, stroke, text)) for a media type."""
    lower = media_name.lower()
    for keyword, colors in MEDIA_COLORS:
        if keyword in lower:
            return "m_" + re.sub(r"[^a-zA-Z0-9]", "_", keyword), colors

    cls = "m_" + re.sub(r"[^a-zA-Z0-9]", "_", media_name)
    if cls not in fallback_state:
        fallback_state[cls] = FALLBACK_COLORS[len(fallback_state) % len(FALLBACK_COLORS)]
    return cls, fallback_state[cls]


def add_row_links(lines, ids, per_row):
    """Invisible links between rows so Mermaid wraps nodes into rows of `per_row`."""
    rows = [ids[i:i + per_row] for i in range(0, len(ids), per_row)]
    for upper, lower in zip(rows, rows[1:]):
        for a, b in zip(upper, lower):
            lines.append(f"    {a} ~~~ {b}")


def generate_mermaid(actions, lookups, sends, stats, direction="TD", width=520,
                     merge=False, per_row=0, elk=False,
                     by_recipient=False, min_actions=2):
    lines = ["---", "config:"]
    if elk:
        lines.append("  layout: elk")
    lines += [
        "  flowchart:",
        f"    wrappingWidth: {width}",
        "    nodeSpacing: 30",
        "    rankSpacing: 80",
        "---",
        f"flowchart {direction}",
        "",
    ]

    action_ids = []
    endpoint_ids = []          # hubs and endpoint blocks, in creation order
    local_endpoints = {}       # (media, names tuple) -> node id
    hubs = {}                  # recipient_key -> node id
    used_styles = {}           # css class -> colors
    fallback_state = {}
    edge_seen = set()
    edge_count = 0
    edge_classes = defaultdict(list)   # css class -> [edge indexes] (for linkStyle)

    def add_edge(src, dst, media_cls, label=None):
        nonlocal edge_count
        key = (src, dst, label)
        if key in edge_seen:
            return
        edge_seen.add(key)
        if label:
            lines.append(f'    {src} -->|"{escape(label)}"| {dst}')
        else:
            lines.append(f"    {src} --> {dst}")
        edge_classes[media_cls].append(edge_count)
        edge_count += 1

    for action in actions:
        aid = action_node_id(action)
        action_ids.append(aid)

        flt = action.get("filter", {})
        conditions = flt.get("conditions", [])
        evaltype = str(flt.get("evaltype", "0"))

        # ---- one block: heading + bulleted conditions ----
        label = f"{LEFT_OPEN}<b>{escape(action['name'])}</b>"
        if conditions:
            label += f"<br/>{DIVIDER}<br/>"
            label += "<br/>".join(format_conditions(conditions, lookups, evaltype, merge))
            if evaltype == "3":
                label += f'<br/><i>Formula: {escape(flt.get("formula", ""))}</i>'
            elif len(conditions) > 1:
                label += f"<br/><i>Match: {EVALTYPES.get(evaltype, evaltype)}</i>"
        else:
            label += "<br/><i>No conditions (all problems)</i>"
        label += LEFT_CLOSE
        lines.append(f'    {aid}["{label}"]:::action')

        # ---- operations -> hubs / endpoint blocks ----
        for media, recips in sends[aid]:
            cls, colors = media_style(media, fallback_state)
            used_styles[cls] = colors

            if by_recipient:
                hub_recips = [r for r in recips if len(stats[r[0]]["actions"]) >= min_actions]
                local_recips = [r for r in recips if len(stats[r[0]]["actions"]) < min_actions]
            else:
                hub_recips, local_recips = [], recips

            # recipient hubs: one node per user/group, media on the edge
            for rkey, rname in hub_recips:
                if rkey not in hubs:
                    hub_id = f"recipient_{len(hubs) + 1}"
                    hubs[rkey] = hub_id
                    endpoint_ids.append(hub_id)
                    n = len(stats[rkey]["actions"])
                    hub_label = (
                        f"{LEFT_OPEN}<b>{escape(rname)}</b><br/>"
                        f"<i>{n} action{'s' if n != 1 else ''}</i>{LEFT_CLOSE}"
                    )
                    lines.append(f'    {hub_id}(["{hub_label}"]):::hub')
                add_edge(aid, hubs[rkey], cls, label=media)

            # everyone else: one endpoint block per media + recipient set
            if local_recips or not recips:
                names = tuple(sorted(r[1] for r in local_recips))
                key = (media, names)
                if key not in local_endpoints:
                    node_id = f"endpoint_{len(local_endpoints) + 1}"
                    local_endpoints[key] = node_id
                    endpoint_ids.append(node_id)

                    ep_label = f"{LEFT_OPEN}<b>{escape(media)}</b><br/>"
                    if names:
                        ep_label += "<br/>".join(f"{BULLET} {escape(r)}" for r in names)
                    else:
                        ep_label += "<i>no recipients</i>"
                    ep_label += LEFT_CLOSE
                    lines.append(f'    {node_id}(["{ep_label}"]):::{cls}')
                add_edge(aid, local_endpoints[key], cls)

        lines.append("")

    # ---- row layout ----
    if per_row:
        add_row_links(lines, action_ids, per_row)
        add_row_links(lines, endpoint_ids, per_row)
        lines.append("")

    # ---- styles ----
    lines.append(
        "    classDef action fill:#f8fafc,stroke:#334155,"
        "stroke-width:1.5px,color:#0f172a"
    )
    lines.append(
        "    classDef hub fill:#f1f5f9,stroke:#475569,"
        "stroke-width:2.5px,color:#0f172a"
    )
    for cls, (fill, stroke, text) in used_styles.items():
        lines.append(
            f"    classDef {cls} fill:{fill},stroke:{stroke},"
            f"stroke-width:2px,color:{text}"
        )

    # linkStyle indexes count every link in order of appearance; the invisible
    # row links are appended after all real edges, so these indexes stay valid.
    for cls, idxs in edge_classes.items():
        stroke = used_styles[cls][1]
        lines.append(
            f"    linkStyle {','.join(map(str, idxs))} stroke:{stroke},stroke-width:2px"
        )

    return "\n".join(lines)


# --------------------------------------------------------------------------
# Markdown table
# --------------------------------------------------------------------------

def generate_markdown(actions, stats):
    names = {action_node_id(a): a["name"] for a in actions}
    lines = [
        "# Zabbix trigger actions: who receives what",
        "",
        "| Recipient | Media | Count | Actions |",
        "|---|---|---|---|",
    ]
    ordered = sorted(
        stats.values(),
        key=lambda s: (-len(s["actions"]), s["name"].lower()),
    )
    for s in ordered:
        for media in sorted(s["media"]):
            acts = sorted(names[a] for a in s["media"][media])
            lines.append(
                f"| {md_escape(s['name'])} | {md_escape(media)} | {len(acts)} | "
                f"{md_escape(', '.join(acts))} |"
            )
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Zabbix trigger actions -> Mermaid flowchart")
    parser.add_argument("--dir", default="TD", choices=["TD", "TB", "LR", "RL", "BT"],
                        help="flowchart direction (TD = wide overview, LR = tall)")
    parser.add_argument("--width", type=int, default=520,
                        help="node wrapping width in px (default 520)")
    parser.add_argument("--merge", action="store_true",
                        help="merge conditions with the same field and operator onto one bullet")
    parser.add_argument("--per-row", type=int, default=0,
                        help="wrap actions (and endpoints) into rows of N nodes")
    parser.add_argument("--elk", action="store_true",
                        help="use the ELK layout engine (better edge routing)")
    parser.add_argument("--by-recipient", action="store_true",
                        help="one hub node per recipient used by several actions, media on the edge")
    parser.add_argument("--min-actions", type=int, default=2,
                        help="with --by-recipient: minimum actions for a recipient to get a hub "
                             "(1 = every recipient)")
    parser.add_argument("--out", default="zabbix-actions.mmd", help="Mermaid output file")
    parser.add_argument("--md-out", default="zabbix-recipients.md",
                        help="Markdown recipient table output file")
    parser.add_argument("--no-md", action="store_true", help="skip the Markdown table")
    args = parser.parse_args()

    url = os.environ.get("ZABBIX_URL", "https://vnk-customerzabbix.abramad.com")
    token = "26cb6260aaf2eef8eaeccaf2343df1c9c12987143b63b4c78415318b0a884cf8" #os.environ["ZABBIX_TOKEN"]  # export ZABBIX_TOKEN=... instead of hardcoding

    zapi = ZabbixAPI(url)
    zapi.login(api_token=token)

    actions = get_actions(zapi)
    lookups = build_lookup_tables(zapi, actions)
    sends = collect_sends(actions, lookups)
    stats = recipient_stats(actions, sends)

    mermaid = generate_mermaid(
        actions, lookups, sends, stats,
        direction=args.dir, width=args.width, merge=args.merge,
        per_row=args.per_row, elk=args.elk,
        by_recipient=args.by_recipient, min_actions=args.min_actions,
    )

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(mermaid)
    print(mermaid)

    if not args.no_md:
        with open(args.md_out, "w", encoding="utf-8") as f:
            f.write(generate_markdown(actions, stats))


if __name__ == "__main__":
    main()