"""ITG Node — The core logic for every ITG entity (Boss or Worker).

Each entity: splits image -> judges quality -> describes good layers ->
writes tailored prompts for children -> (if Boss: creates child tasks, if Worker: uploads final result).
"""

import os, sys, json, time, uuid, tempfile
import requests as http_requests

sys.path.insert(0, os.path.dirname(__file__))
from itg_splitter import split_image_into_n_layers
from itg_judge import judge_layer_quality, determine_z_order
from itg_logger import itg_log, itg_error


class ITGNode:
    """
    Represents one entity in the ITG system.

    In ITG, everyone does the same work — there is no difference between
    Boss and Worker except position in the hierarchy. This class handles both roles.
    """

    def __init__(self, server_url, node_id, comfyui_port=8188, vision_model="qwen3-vl:4b",
                 llm_model="qwen3:14b", llm_provider="ollama"):
        self.server_url = server_url.rstrip("/")
        self.node_id = node_id
        self.comfyui_port = comfyui_port
        self.vision_model = vision_model
        self.llm_model = llm_model
        self.llm_provider = llm_provider
        self.output_dir = os.path.join(os.path.dirname(__file__), "output", "itg", node_id)
        os.makedirs(self.output_dir, exist_ok=True)

    def _api(self, method, path, **kwargs):
        url = f"{self.server_url}{path}"
        kwargs.setdefault("timeout", 30)
        if method == "GET":
            return http_requests.get(url, **kwargs)
        elif method == "POST":
            return http_requests.post(url, **kwargs)
        elif method == "PUT":
            return http_requests.put(url, **kwargs)
        elif method == "DELETE":
            return http_requests.delete(url, **kwargs)

    def poll_for_task(self):
        """Check for pending ITG tasks. Returns task dict or None."""
        resp = self._api("GET", "/api/tasks?status=pending&type=ITG")
        if not resp.ok:
            return None
        tasks = resp.json()
        if not tasks:
            return None
        return tasks[0]

    def claim_and_process(self, task):
        """Claim a task, process it, and upload results."""
        # Claim
        resp = self._api("POST", f"/api/task/{task['id']}/claim",
                         json={"worker_id": self.node_id})
        if not resp.ok:
            print(f"Claim failed: {resp.text}", flush=True)
            return False

        task = resp.json()
        print(f"\n=== ITG Node '{self.node_id}' claimed Task #{task['id']} ===", flush=True)
        print(f"  Depth: {task.get('depth', 0)}, Input: {task.get('input_image', '?')}", flush=True)

        # Download input image from server
        input_image = task.get("input_image", "")
        if input_image:
            img_resp = self._api("GET", f"/api/files/{input_image}")
            if img_resp.ok:
                input_path = os.path.join(self.output_dir, input_image)
                with open(input_path, "wb") as f:
                    f.write(img_resp.content)
            else:
                print(f"  WARNING: Could not download input image {input_image}", flush=True)
                input_path = None
        else:
            input_path = None

        if not input_path or not os.path.exists(input_path):
            print("  No input image — skipping split.", flush=True)
            return False

        # Split with Qwen-Image-Layered
        print(f"  Splitting {input_path}...", flush=True)
        try:
            layer_files = split_image_into_n_layers(
                input_path, self.output_dir, n=2, steps=20, cfg=4.0,
                comfyui_port=self.comfyui_port,
                prompt=task.get("prompt", ""),
            )
            itg_log(self.node_id, "SPLIT_DONE", task["id"], f"{len(layer_files)} layers")
        except Exception as e:
            print(f"  Split FAILED: {e}", flush=True)
            self._api("POST", f"/api/task/{task['id']}/reset")
            return False

        if len(layer_files) != 2:
            print(f"  WARNING: Expected 2 layers, got {len(layer_files)}", flush=True)
            if not layer_files:
                self._api("POST", f"/api/task/{task['id']}/reset")
                return False

        # Judge quality
        good_layers = []
        garbage_layers = []
        good_judgments = []  # save judgments to avoid re-calling Ollama in child prompt step
        for i, lf in enumerate(layer_files):
            judgment = judge_layer_quality(lf, model=self.vision_model,
                                           parent_description=f"Sub-part {i+1} from: {input_image}")
            print(f"  Layer {i+1}: {judgment['quality']} — {judgment['description'][:60]}", flush=True)
            if judgment["quality"] == "good":
                good_layers.append(lf)
                good_judgments.append(judgment)
            else:
                garbage_layers.append(lf)

        # Handle dual-garbage
        if not good_layers:
            retry_count = task.get("retry_count", 0) + 1
            if retry_count >= 3:
                print(f"  3 dual-garbage retries — marking branch dead.", flush=True)
                self._api("PUT", f"/api/task/{task['id']}",
                          json={"status": "failed"})
                return False

            print(f"  Dual-garbage (retry {retry_count}/3). Creating fallback child.", flush=True)
            # Re-upload original input as fallback child
            child_task = {
                "question_id": task["question_id"],
                "type": "ITG",
                "parent_task_id": task["id"],
                "depth": (task.get("depth", 0) or 0) + 1,
                "max_depth": task.get("max_depth", 2),
                "prompt": "",
                "input_image": task.get("input_image", ""),
                "retry_count": retry_count,
            }
            self._api("POST", "/api/tasks/batch", json={"tasks": [child_task]})
            return True

        # Upload good layers to server
        uploaded_filenames = []
        for i, lf in enumerate(good_layers):
            with open(lf, "rb") as f:
                resp = self._api("POST", "/api/files/upload",
                                 files={"file": f},
                                 data={"task_id": str(task["id"])})
                if resp.ok:
                    uploaded_filenames.append(resp.json()["filename"])

        # Decide: are we at max depth?
        depth = task.get("depth", 0) or 0
        max_depth = task.get("max_depth", 2) or 2

        if depth >= max_depth:
            # WE ARE A WORKER (bottom) — upload final results
            print(f"  Depth {depth} >= {max_depth} — uploading as final.", flush=True)
            files = []
            for fn in uploaded_filenames:
                filepath = os.path.join(self.output_dir, fn)
                if os.path.exists(filepath):
                    files.append(("images", (fn, open(filepath, "rb"), "image/png")))

            if files:
                resp = self._api("POST", f"/api/task/{task['id']}/result", files=files)
                if resp.ok:
                    print(f"  Final results uploaded for Task #{task['id']}.", flush=True)
            return True
        else:
            # WE ARE A BOSS — create child tasks with tailored prompts
            print(f"  Depth {depth} < {max_depth} — creating {len(good_layers)} child tasks.", flush=True)

            child_tasks = []
            for i, (lf, fn, judgment) in enumerate(zip(good_layers, uploaded_filenames, good_judgments)):
                desc = judgment.get("description", "")
                child_prompt = f"Decompose this layer further: {desc}" if desc else ""

                child_tasks.append({
                    "question_id": task["question_id"],
                    "type": "ITG",
                    "parent_task_id": task["id"],
                    "depth": depth + 1,
                    "max_depth": max_depth,
                    "prompt": child_prompt,
                    "input_image": fn,
                })

            if child_tasks:
                resp = self._api("POST", "/api/tasks/batch", json={"tasks": child_tasks})
                if resp.ok:
                    print(f"  {len(child_tasks)} child tasks created.", flush=True)

            # Mark current task complete
            # (In ITG, the Boss task is complete once children are created)
            self._api("POST", f"/api/task/{task['id']}/result",
                      data={"split_result_1": uploaded_filenames[0] if len(uploaded_filenames) > 0 else "",
                            "split_result_2": uploaded_filenames[1] if len(uploaded_filenames) > 1 else ""})
            return True

    def _generate_child_prompt(self, layer_path, parent_task):
        """
        Use Qwen3-VL to describe the layer, then use description as the child's split prompt.

        In production: Qwen LLM should generate a structured split prompt
        (e.g., "Decompose into: glass base, metal stem, smoke wisps").
        For now: use the Qwen3-VL description directly.
        """
        judgment = judge_layer_quality(layer_path, model=self.vision_model)
        desc = judgment.get("description", "")
        if desc:
            return f"Decompose this layer further: {desc}"
        return ""

    def run_once(self):
        """Single polling cycle. Returns True if processed a task, False if idle."""
        task = self.poll_for_task()
        if task:
            return self.claim_and_process(task)
        return False

    def run_loop(self, poll_interval=5):
        """Continuous polling loop."""
        print(f"ITG Node '{self.node_id}' started. Polling every {poll_interval}s.", flush=True)
        while True:
            try:
                processed = self.run_once()
                if not processed:
                    time.sleep(poll_interval)
            except KeyboardInterrupt:
                print("ITG Node stopped.", flush=True)
                break
            except Exception as e:
                print(f"Error in ITG node loop: {e}", flush=True)
                time.sleep(poll_interval)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ITG Node — Image To Ghost worker/boss")
    parser.add_argument("--server", default="http://localhost:5000", help="Flask server URL")
    parser.add_argument("--id", default="itg-node-1", help="Node ID")
    parser.add_argument("--comfyui-port", type=int, default=8188, help="ComfyUI port")
    parser.add_argument("--vision-model", default="qwen3-vl:4b", help="Qwen3-VL model for Ollama")
    parser.add_argument("--once", action="store_true", help="Process one task and exit")

    args = parser.parse_args()

    node = ITGNode(
        server_url=args.server,
        node_id=args.id,
        comfyui_port=args.comfyui_port,
        vision_model=args.vision_model,
    )

    if args.once:
        node.run_once()
    else:
        node.run_loop()
