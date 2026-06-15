#!/usr/bin/env python3
"""
Copy folders+dashboards from multiple Grafana orgs into a single managers org,
and translate datasource UIDs/names from each source org to the Managers org
so imported dashboards keep working.

Put your tokens in SRC_ORG_TOKENS and DST_ORG_TOKENS["Managers"].
"""
import requests
import time
import copy
import sys

#GRAFANA_URL = "https://me-grafana.abramad.com"  # <- change to your Grafana base URL (no trailing slash)
GRAFANA_URL = "https://vnk-grafana.abramad.com"

# map of source org name -> token (source token must be able to read folders/dashboards)
SRC_ORG_TOKENS = {
    # ME-Grafana
    # "Main Org.": "xyz",
}

# token for target organization (must have folders:write and dashboards:write)
DST_ORG_TOKENS = {
    # ME-Grafana
    # "Managers": "xyz",
    # VNK-Grafana
    "Managers": "xyz",
}

# behavior switches
PRESERVE_DASHBOARD_UIDS = False    # set to True if you want to preserve original dashboard uids (may cause collisions)
OVERWRITE_EXISTING = False         # if True, dashboards with same uid will be overwritten in managers org
PRESERVE_FOLDER_UIDS = False       # same idea for folder UIDs
DRY_RUN = False                    # if True, do not POST dashboards/folders; only print actions

DST_ORG_TOKEN = DST_ORG_TOKENS.get("Managers")

def hdr(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# ---------------- Grafana API helpers ----------------

def get_folders(token):
    url = f"{GRAFANA_URL}/api/folders"
    r = requests.get(url, headers=hdr(token))
    r.raise_for_status()
    print(f"get_folders output:\n\n{r.json()}\n")
    return r.json()

def get_dashboards_in_folder(token, folder_id):
    """
    Return list of dashboards for the given numeric folder_id (as returned by /api/folders).
    Uses /api/search with params; if that returns empty, falls back to retrieving all dashboards
    in the org and filtering by folderId locally.
    """
    url = f"{GRAFANA_URL}/api/search"
    params = {
        "type": "dash-db",
        "folderIds": str(folder_id),
        "limit": 5000,
        "query": ""   # explicit empty query helps some Grafana versions
    }
    try:
        r = requests.get(url, headers=hdr(token), params=params)
        print(f"GET {r.request.url} -> {r.status_code}")
        try:
            js = r.json()
        except Exception:
            print("Non-JSON response from /api/search:", r.text[:1000])
            r.raise_for_status()
        if r.status_code != 200:
            print("Non-200 response from /api/search:", r.status_code, js)
            r.raise_for_status()

        print(f"get_dashboards_in_folder primary output (len={len(js)}):\n{js}\n")
        if js:
            return js

        # fallback: request all dashboards and filter locally
        print(f"/api/search returned empty for folder {folder_id}, fetching all dashboards and filtering as fallback...")
        params_all = {
            "type": "dash-db",
            "limit": 5000,
            "query": ""
        }
        r2 = requests.get(url, headers=hdr(token), params=params_all)
        print(f"GET {r2.request.url} -> {r2.status_code}")
        r2.raise_for_status()
        try:
            all_dashboards = r2.json()
        except Exception:
            print("Non-JSON response from fallback /api/search:", r2.text[:1000])
            raise

        filtered = []
        for item in all_dashboards:
            if ("folderId" in item and item.get("folderId") == folder_id) or (item.get("folderId") == str(folder_id)):
                filtered.append(item)
        print(f"Fallback filtered dashboards (len={len(filtered)}).")
        return filtered

    except requests.HTTPError:
        print("HTTP error calling /api/search (primary). Response body (if available):")
        try:
            print(r.json())
        except Exception:
            print(r.text)
        raise
    except Exception as e:
        print("Unexpected error in get_dashboards_in_folder:", e)
        raise

def get_dashboard_by_uid(token, uid):
    url = f"{GRAFANA_URL}/api/dashboards/uid/{uid}"
    r = requests.get(url, headers=hdr(token))
    r.raise_for_status()
    return r.json()  # {"meta":..., "dashboard": {...}}

def create_folder_in_org(token, title, uid=None, parentUid=None):
    body = {"title": title}
    if uid and PRESERVE_FOLDER_UIDS:
        body["uid"] = uid
    if parentUid:
        body["parentUid"] = parentUid
    url = f"{GRAFANA_URL}/api/folders"
    if DRY_RUN:
        print("[dry-run] create folder payload:", body)
        return {"uid": f"dry-{title}"}
    r = requests.post(url, headers=hdr(token), json=body)
    if r.status_code == 412 or r.status_code == 200:
        try:
            return r.json()
        except:
            return {"status": r.status_code, "text": r.text}
    # print debug on failure
    if r.status_code >= 400:
        print("create_folder_in_org failed: status", r.status_code)
        try:
            print("response:", r.json())
        except:
            print("response text:", r.text)
    r.raise_for_status()
    return r.json()

def find_folder_by_title(token, title):
    folders = get_folders(token)
    for f in folders:
        if f.get("title") == title:
            return f
    return None

def import_dashboard_to_org(token, dashboard_json, folderUid, overwrite=False):
    payload = {
        "dashboard": dashboard_json,
        "folderUid": folderUid,
        "overwrite": overwrite
    }
    url = f"{GRAFANA_URL}/api/dashboards/db"
    if DRY_RUN:
        print("[dry-run] import payload title:", dashboard_json.get("title"), "folderUid:", folderUid)
        return {"uid": f"dry-{dashboard_json.get('title')}"}
    r = requests.post(url, headers=hdr(token), json=payload)
    if r.status_code >= 400:
        print("import_dashboard_to_org failed:", r.status_code)
        try:
            print("response:", r.json())
        except:
            print("response text:", r.text)
    r.raise_for_status()
    return r.json()

# ---------------- Datasource mapping helpers ----------------

def get_datasources(token):
    """Return list of datasources in the org for token."""
    url = f"{GRAFANA_URL}/api/datasources"
    r = requests.get(url, headers=hdr(token))
    r.raise_for_status()
    return r.json()

def build_datasource_mapping(src_token, dst_token, overrides=None):
    """
    Build mapping from source datasource uid/name -> destination datasource uid.
    Returns mapping dict and list of unmatched source datasources.
    """
    overrides = overrides or {}

    src_ds = get_datasources(src_token)
    dst_ds = get_datasources(dst_token)

    dst_by_name = {d["name"]: d for d in dst_ds}
    dst_by_name_ci = {d["name"].lower(): d for d in dst_ds}
    dst_by_uid = {d["uid"]: d for d in dst_ds}

    mapping = {}
    unmatched = []

    for s in src_ds:
        s_uid = s.get("uid")
        s_name = s.get("name")
        s_type = s.get("type")

        # exact name match
        if s_name in dst_by_name:
            mapping[s_uid] = dst_by_name[s_name]["uid"]
            mapping[s_name] = dst_by_name[s_name]["uid"]
            continue
        # case-insensitive name match
        if s_name and s_name.lower() in dst_by_name_ci:
            d = dst_by_name_ci[s_name.lower()]
            mapping[s_uid] = d["uid"]
            mapping[s_name] = d["uid"]
            continue
        # type + lower name
        matched = False
        for d in dst_ds:
            if d.get("type") == s_type and d.get("name","").lower() == (s_name or "").lower():
                mapping[s_uid] = d["uid"]
                mapping[s_name] = d["uid"]
                matched = True
                break
        if matched:
            continue

        # not matched automatically
        unmatched.append({"uid": s_uid, "name": s_name, "type": s_type})

    # apply overrides (explicit user mapping): key=src_name_or_uid -> value=dst_uid
    for k, v in overrides.items():
        mapping[k] = v

    return mapping, unmatched

def replace_datasource_refs(obj, mapping, dst_ds_by_uid=None):
    """
    Recursively walk dashboard JSON and replace datasource references.
    mapping: source uid or source name -> destination uid
    dst_ds_by_uid: optional dict mapping dst uid -> name (used for adding names)
    Returns transformed object (new copy).
    """
    if dst_ds_by_uid is None:
        dst_ds_by_uid = {}

    if isinstance(obj, dict):
        new = {}
        for k, v in obj.items():
            # keys that commonly reference datasources
            if k in ("datasource", "datasourceUid"):
                # dict case
                if isinstance(v, dict):
                    src_uid = v.get("uid")
                    src_name = v.get("name")
                    dst_uid = None
                    if src_uid and src_uid in mapping:
                        dst_uid = mapping[src_uid]
                    elif src_name and src_name in mapping:
                        dst_uid = mapping[src_name]
                    if dst_uid:
                        new[k] = {"uid": dst_uid}
                        if dst_ds_by_uid.get(dst_uid):
                            new[k]["name"] = dst_ds_by_uid[dst_uid]
                        continue
                    else:
                        new[k] = v
                        continue

                # string case
                if isinstance(v, str):
                    if v in mapping:
                        new[k] = {"uid": mapping[v]}
                        if dst_ds_by_uid.get(mapping[v]):
                            new[k]["name"] = dst_ds_by_uid[mapping[v]]
                        continue
                    else:
                        # keep as-is if not mapped
                        new[k] = v
                        continue

                # otherwise, recurse
                new[k] = replace_datasource_refs(v, mapping, dst_ds_by_uid)
                continue

            # other keys: recurse
            new[k] = replace_datasource_refs(v, mapping, dst_ds_by_uid)
        return new

    if isinstance(obj, list):
        return [replace_datasource_refs(i, mapping, dst_ds_by_uid) for i in obj]

    # primitives
    return obj

def collect_datasource_refs(d):
    """Collect datasource references (names or uids) in dashboard JSON for reporting."""
    refs = set()
    if isinstance(d, dict):
        for k, v in d.items():
            if k in ("datasource", "datasourceUid"):
                if isinstance(v, dict):
                    if v.get("uid"):
                        refs.add(v.get("uid"))
                    elif v.get("name"):
                        refs.add(v.get("name"))
                elif isinstance(v, str):
                    refs.add(v)
            else:
                refs |= collect_datasource_refs(v)
    elif isinstance(d, list):
        for i in d:
            refs |= collect_datasource_refs(i)
    return refs

# ---------------- Body ----------------

if not SRC_ORG_TOKENS:
    print("Fill SRC_ORG_TOKENS and set GRAFANA_URL and DST_ORG_TOKENS")
    sys.exit(1)
if not DST_ORG_TOKEN:
    print("Managers token missing in DST_ORG_TOKENS['Managers']")
    sys.exit(1)

managers_token = DST_ORG_TOKEN
folder_map = {}  # (source_org, source_folder_uid) -> managers_folder_uid

for org_name, src_token in SRC_ORG_TOKENS.items():
    print(f"\n=== Processing source org: {org_name} ===")

    # build datasource mapping for this source org -> Managers
    print("Building datasource mapping for", org_name)
    # If you need to provide overrides, put them here as {"src-name-or-uid": "dst-uid", ...}
    overrides = {}
    ds_mapping, ds_unmatched = build_datasource_mapping(src_token, managers_token, overrides=overrides)
    dst_ds = get_datasources(managers_token)
    dst_uid_to_name = {d["uid"]: d["name"] for d in dst_ds}

    print("Datasource mapping (sample):")
    # print only a few mapping lines for brevity
    sample_items = list(ds_mapping.items())[:20]
    for k, v in sample_items:
        print("  ", k, "->", v)
    if ds_unmatched:
        print("Unmatched source datasources (you may want to create/match these in Managers):")
        for u in ds_unmatched:
            print("  ", u)
    else:
        print("All source datasources matched automatically (by name or heuristics).")

    # create/find top-level folder inside managers with source org name
    root_title = org_name
    existing = find_folder_by_title(managers_token, root_title)
    if existing:
        print(f"Found existing root folder in managers: {root_title} (uid={existing.get('uid')})")
        managers_root_uid = existing.get("uid")
    else:
        created = create_folder_in_org(managers_token, root_title, uid=None)
        managers_root_uid = created.get("uid")
        print(f"Created root folder in managers: {root_title} (uid={managers_root_uid})")

    # get all folders in source org
    try:
        src_folders = get_folders(src_token)
    except Exception as e:
        print(f"Failed to list folders in source org {org_name}: {e}")
        continue

    src_folder_by_uid = {f["uid"]: f for f in src_folders}

    # create corresponding folders in managers (preserve parent/children relationship)
    pending = list(src_folders)
    created_map = {}
    created_map[None] = managers_root_uid

    loop_guard = 0
    while pending and loop_guard < 10000:
        loop_guard += 1
        f = pending.pop(0)
        src_uid = f.get("uid")
        title = f.get("title")
        parent_uid = f.get("parentUid") if f.get("parentUid") else None
        if parent_uid and parent_uid not in created_map:
            pending.append(f)
            continue
        parent_managers_uid = created_map.get(parent_uid, managers_root_uid)
        new_title = title
        created = None
        try:
            existing = find_folder_by_title(managers_token, new_title)
            if existing:
                created = existing
            else:
                created = create_folder_in_org(managers_token, new_title, uid=(src_uid if PRESERVE_FOLDER_UIDS else None), parentUid=parent_managers_uid)
        except Exception as e:
            print(f"Failed creating folder {new_title} in managers: {e}")
            pending.append(f)
            time.sleep(1)
            continue

        created_uid = created.get("uid")
        created_map[src_uid] = created_uid
        folder_map[(org_name, src_uid)] = created_uid
        print(f"-> Folder created/mapped: src '{title}' (uid={src_uid}) -> managers uid {created_uid}")

    # now iterate all dashboards in each source folder and import them
    for src_folder in src_folders:
        fid = src_folder.get("id")
        fuid = src_folder.get("uid")
        dash_list = []
        try:
            dash_list = get_dashboards_in_folder(src_token, fid)
        except Exception as e:
            print(f"Failed listing dashboards in folder {src_folder.get('title')}: {e}")
            continue

        print(f"Folder '{src_folder.get('title')}' contains {len(dash_list)} dashboards")
        for dmeta in dash_list:
            try:
                dash_uid = dmeta.get("uid")
                print("Processing dashboard:", dmeta.get("title"), "uid:", dash_uid)
                full = get_dashboard_by_uid(src_token, dash_uid)
                dashboard = full.get("dashboard")
                if not dashboard:
                    print("No 'dashboard' object found in response for", dash_uid)
                    continue

                # sanitize
                if "id" in dashboard:
                    del dashboard["id"]
                if not PRESERVE_DASHBOARD_UIDS:
                    if "uid" in dashboard:
                        dashboard["uid"] = None

                # Replace datasource references using mapping
                transformed = replace_datasource_refs(dashboard, ds_mapping, dst_ds_by_uid=dst_uid_to_name)

                # report any used datasource refs that are not mapped
                used = collect_datasource_refs(transformed)
                # built set of destination uids and source names/uids in mapping
                mapped_values = set(ds_mapping.values())
                mapped_keys = set(ds_mapping.keys())
                unmapped_used = []
                for r in used:
                    # If reference is already a destination uid (exists in dst uid list), it's OK
                    if r in dst_uid_to_name:
                        continue
                    # If reference is source-name/uid and mapped -> OK
                    if r in mapped_keys:
                        continue
                    # If reference maps to a destination uid (via mapping) then OK
                    if r in mapped_values:
                        continue
                    # else, report as unmapped
                    unmapped_used.append(r)
                if unmapped_used:
                    print("WARNING: dashboard references datasources not mapped (may show 'No data'):", unmapped_used)
                    # Note: we continue and attempt import - you'll need to create or map these datasources in Managers

                target_folder_uid = created_map.get(fuid, managers_root_uid)
                res = import_dashboard_to_org(managers_token, transformed, folderUid=target_folder_uid, overwrite=OVERWRITE_EXISTING)
                print(f"Imported dashboard '{dashboard.get('title')}' -> {res.get('uid')}")
            except Exception as e:
                print(f"Failed to import dashboard {dmeta.get('title')} (uid {dmeta.get('uid')}): {e}")
                continue

print("\nAll done.")
