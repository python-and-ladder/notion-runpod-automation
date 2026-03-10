"""Streamlit version of the RunPod Pod Manager."""

import json
from pathlib import Path

import requests
import runpod
import streamlit as st

CONFIG_PATH = Path(__file__).parent / "config.json"

TEMPLATES_URL = "https://rest.runpod.io/v1/templates"


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def save_config(data: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def get_display_status(pod: dict) -> str:
    status = pod.get("desiredStatus", "UNKNOWN")
    runtime = pod.get("runtime")
    if runtime and status == "RUNNING":
        return "RUNNING"
    if status == "RUNNING" and not runtime:
        return "STARTING"
    return status


def get_ssh_info(pod: dict) -> dict:
    runtime = pod.get("runtime") or {}
    ports = runtime.get("ports") or []
    for p in ports:
        if p.get("privatePort") == 22 and p.get("isIpPublic"):
            ip = p.get("ip")
            port = p.get("publicPort")
            if ip and port:
                return {
                    "ip": str(ip),
                    "port": str(port),
                    "command": f"ssh root@{ip} -p {port} -i ~/.ssh/id_ed25519",
                }
    status = pod.get("desiredStatus", "UNKNOWN")
    note = "(pod not running)" if status != "RUNNING" else "(no public SSH port found)"
    return {"ip": None, "port": None, "command": None, "note": note}


def fetch_pods() -> list[dict]:
    pods = runpod.get_pods()
    return pods if isinstance(pods, list) else []


def fetch_templates(api_key: str) -> list[dict]:
    resp = requests.get(
        TEMPLATES_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        params={"includeRunpodTemplates": "true"},
        timeout=30,
    )
    resp.raise_for_status()
    templates = resp.json()
    if not isinstance(templates, list):
        return []
    return [t for t in templates if not t.get("isServerless")]


def fetch_gpus() -> list[dict]:
    gpus = runpod.get_gpus()
    return gpus if isinstance(gpus, list) else []


def _get_api_key() -> str:
    return st.session_state.get("_api_key", "").strip()


def _ensure_api_key() -> str | None:
    """Return the active API key or show a warning and return None."""
    key = _get_api_key()
    if not key:
        st.warning("Enter your API key in the sidebar first.")
        return None
    runpod.api_key = key
    return key


def _refresh_pods():
    key = _ensure_api_key()
    if key:
        st.session_state.pods = fetch_pods()


# ---------------------------------------------------------------------------
# Page config & session state
# ---------------------------------------------------------------------------

st.set_page_config(page_title="RunPod Pod Manager", layout="wide")
st.title("RunPod Pod Manager")

for key, default in [("pods", []), ("templates", []), ("gpus", [])]:
    if key not in st.session_state:
        st.session_state[key] = default

cfg = load_config()
saved_key = cfg.get("api_key", "")

# ---------------------------------------------------------------------------
# Sidebar – API key
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("RunPod API Key")
    api_key = st.text_input(
        "API Key",
        value=saved_key,
        type="password",
        placeholder="Paste your RunPod API key here...",
        key="_api_key",
    )
    if st.button("Save & Connect", use_container_width=True):
        key = api_key.strip()
        if not key:
            st.error("Please enter a RunPod API key.")
        else:
            save_config({"api_key": key})
            runpod.api_key = key
            with st.spinner("Connecting..."):
                errors = []
                try:
                    st.session_state.pods = fetch_pods()
                except Exception as exc:
                    errors.append(f"Pods: {exc}")
                try:
                    st.session_state.templates = fetch_templates(key)
                except Exception as exc:
                    errors.append(f"Templates: {exc}")
                try:
                    st.session_state.gpus = fetch_gpus()
                except Exception as exc:
                    errors.append(f"GPUs: {exc}")

                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    st.success(
                        f"Loaded {len(st.session_state.pods)} pod(s), "
                        f"{len(st.session_state.templates)} template(s), "
                        f"{len(st.session_state.gpus)} GPU type(s)"
                    )

# Auto-connect on first load when a saved key exists
if saved_key and not st.session_state.pods:
    runpod.api_key = saved_key
    try:
        st.session_state.pods = fetch_pods()
    except Exception:
        pass
    try:
        st.session_state.templates = fetch_templates(saved_key)
    except Exception:
        pass
    try:
        st.session_state.gpus = fetch_gpus()
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_pods, tab_create = st.tabs(["My Pods", "Create Pod"])

# ============================= TAB: MY PODS ===============================

with tab_pods:
    pods = st.session_state.pods

    if not pods:
        st.info(
            "No pods loaded. Enter your API key in the sidebar and "
            "click **Save & Connect**."
        )
    else:
        st.subheader("Pods")

        table_rows = []
        for pod in pods:
            machine = pod.get("machine", {}) or {}
            gpu = machine.get("gpuDisplayName", pod.get("gpuDisplayName", ""))
            table_rows.append({
                "Name": pod.get("name", ""),
                "ID": pod.get("id", ""),
                "Status": get_display_status(pod),
                "GPU": gpu,
                "GPUs": pod.get("gpuCount", 1),
            })

        event = st.dataframe(
            table_rows,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )

        manual_pod_id = st.text_input(
            "Manual Pod ID",
            placeholder="Enter a pod ID to override table selection",
        )

        selected_pod_id: str | None = None
        selected_gpu_count: int = 1
        if manual_pod_id.strip():
            selected_pod_id = manual_pod_id.strip()
        elif event.selection and event.selection.rows:
            row_idx = event.selection.rows[0]
            selected_pod_id = pods[row_idx].get("id")
            selected_gpu_count = pods[row_idx].get("gpuCount", 1)

        # --- Action buttons ---
        col_start, col_stop, col_term, col_refresh = st.columns(4)

        with col_start:
            if st.button("Start Pod", use_container_width=True):
                if not selected_pod_id:
                    st.warning("Select a pod first.")
                else:
                    key = _ensure_api_key()
                    if key:
                        with st.spinner(f"Starting pod {selected_pod_id}..."):
                            try:
                                runpod.resume_pod(selected_pod_id, gpu_count=selected_gpu_count)
                                st.success(f"Pod {selected_pod_id} started")
                                _refresh_pods()
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Error starting pod: {exc}")

        with col_stop:
            if st.button("Stop Pod", use_container_width=True):
                if not selected_pod_id:
                    st.warning("Select a pod first.")
                else:
                    key = _ensure_api_key()
                    if key:
                        with st.spinner(f"Stopping pod {selected_pod_id}..."):
                            try:
                                runpod.stop_pod(selected_pod_id)
                                st.success(f"Pod {selected_pod_id} stopped")
                                _refresh_pods()
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Error stopping pod: {exc}")

        with col_term:
            if st.button("Terminate Pod", type="primary", use_container_width=True):
                if not selected_pod_id:
                    st.warning("Select a pod first.")
                else:
                    st.session_state["_confirm_terminate"] = selected_pod_id

        with col_refresh:
            if st.button("Refresh", use_container_width=True):
                key = _ensure_api_key()
                if key:
                    with st.spinner("Refreshing..."):
                        _refresh_pods()
                        st.rerun()

        # Terminate confirmation
        if st.session_state.get("_confirm_terminate"):
            tid = st.session_state["_confirm_terminate"]
            st.warning(
                f"Are you sure you want to **permanently terminate** pod `{tid}`? "
                "All data on the container disk will be lost."
            )
            c_yes, c_no = st.columns(2)
            with c_yes:
                if st.button("Yes, terminate", type="primary", use_container_width=True):
                    key = _ensure_api_key()
                    if key:
                        try:
                            runpod.terminate_pod(tid)
                            st.success(f"Pod {tid} terminated")
                            st.session_state.pop("_confirm_terminate", None)
                            _refresh_pods()
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Error terminating pod: {exc}")
            with c_no:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.pop("_confirm_terminate", None)
                    st.rerun()

        # --- SSH connection info ---
        if selected_pod_id:
            st.subheader("SSH Connection Info")

            target_pod = None
            for pod in pods:
                if pod.get("id") == selected_pod_id:
                    target_pod = pod
                    break

            if target_pod is None and manual_pod_id.strip():
                try:
                    target_pod = runpod.get_pod(selected_pod_id)
                except Exception:
                    target_pod = None

            if target_pod:
                ssh = get_ssh_info(target_pod)
                if ssh["ip"]:
                    col_ip, col_port = st.columns(2)
                    col_ip.metric("IP", ssh["ip"])
                    col_port.metric("Port", ssh["port"])
                    st.code(ssh["command"], language="bash")
                else:
                    st.warning(ssh.get("note", "SSH info unavailable"))
            else:
                st.warning(f"Could not fetch details for pod `{selected_pod_id}`")

# ============================ TAB: CREATE POD =============================

with tab_create:
    templates = st.session_state.templates
    gpus = st.session_state.gpus

    if not templates and not gpus:
        st.info(
            "No templates or GPUs loaded. Enter your API key in the sidebar "
            "and click **Save & Connect**."
        )
    else:
        st.subheader("Create a New Pod")

        # --- Template selector ---
        template_options = {
            t["id"]: f"{t.get('name', 'Unnamed')}  —  {t.get('imageName', '')}"
            for t in templates
        }
        selected_template_id = st.selectbox(
            "Template",
            options=list(template_options.keys()),
            format_func=lambda tid: template_options.get(tid, tid),
            index=None,
            placeholder="Select a template...",
        )

        selected_template: dict | None = None
        if selected_template_id:
            selected_template = next(
                (t for t in templates if t["id"] == selected_template_id), None
            )

        # --- GPU selector ---
        gpu_options = {g.get("id", ""): g.get("displayName", g.get("id", "")) for g in gpus}
        selected_gpu_id = st.selectbox(
            "GPU Type",
            options=list(gpu_options.keys()),
            format_func=lambda gid: gpu_options.get(gid, gid),
            index=None,
            placeholder="Select a GPU type...",
        )

        # --- Configuration form ---
        st.markdown("---")
        st.subheader("Configuration")

        default_disk = (
            selected_template.get("containerDiskInGb", 20) if selected_template else 20
        )
        default_vol = (
            selected_template.get("volumeInGb", 0) if selected_template else 0
        )

        pod_name = st.text_input("Pod Name", placeholder="my-pod")
        col_gpu_count, col_cloud = st.columns(2)
        with col_gpu_count:
            gpu_count = st.number_input("GPU Count", min_value=1, max_value=8, value=1)
        with col_cloud:
            cloud_type = st.selectbox("Cloud Type", ["ALL", "SECURE", "COMMUNITY"])

        col_disk, col_vol = st.columns(2)
        with col_disk:
            container_disk = st.number_input(
                "Container Disk (GB)", min_value=1, value=default_disk
            )
        with col_vol:
            volume = st.number_input("Volume (GB)", min_value=0, value=default_vol)

        # Show template details when selected
        if selected_template:
            with st.expander("Template details"):
                st.json({
                    "id": selected_template.get("id"),
                    "name": selected_template.get("name"),
                    "image": selected_template.get("imageName"),
                    "ports": selected_template.get("ports"),
                    "containerDiskInGb": selected_template.get("containerDiskInGb"),
                    "volumeInGb": selected_template.get("volumeInGb"),
                    "volumeMountPath": selected_template.get("volumeMountPath"),
                    "env": selected_template.get("env"),
                })

        # --- Create button ---
        st.markdown("---")
        if st.button("Create Pod", type="primary", use_container_width=True):
            if not pod_name.strip():
                st.error("Pod name is required.")
            elif not selected_template_id:
                st.error("Select a template.")
            elif not selected_gpu_id:
                st.error("Select a GPU type.")
            else:
                key = _ensure_api_key()
                if key:
                    with st.spinner("Creating pod..."):
                        try:
                            result = runpod.create_pod(
                                name=pod_name.strip(),
                                template_id=selected_template_id,
                                gpu_type_id=selected_gpu_id,
                                gpu_count=gpu_count,
                                cloud_type=cloud_type,
                                container_disk_in_gb=container_disk,
                                volume_in_gb=volume,
                                support_public_ip=True,
                                start_ssh=True,
                            )
                            new_id = result.get("id", "unknown") if isinstance(result, dict) else "unknown"
                            st.success(f"Pod created! ID: `{new_id}`")
                            _refresh_pods()
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Error creating pod: {exc}")
