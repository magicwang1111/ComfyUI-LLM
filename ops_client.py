"""TikTok operations API client and durable local delivery queue (standard library only)."""

import argparse
import base64
import hashlib
import json
import mimetypes
import os
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

if __package__:
    from .fashion_prompt import read_generation_copy
else:
    from fashion_prompt import read_generation_copy

ROOT = Path(__file__).resolve().parent


def settings(config):
    value = config.get("tiktok_ops", {})
    path = Path(value.get("outbox", "data/ops-outbox.sqlite3")).expanduser()
    return {
        **value,
        "enabled": bool(value.get("enabled", False)),
        "outbox": path.resolve() if path.is_absolute() else (ROOT / path).resolve(),
        "sheet": value.get("sheet", "bnmb"),
    }


def request(options, path, method="GET", data=None, raw=False):
    url = options.get("base_url", "").rstrip("/")
    token = options.get("token", "")
    if not url.startswith(("http://", "https://")) or len(token) < 32:
        raise ValueError(
            "Configure tiktok_ops.base_url and a service token of at least 32 characters."
        )
    body = json.dumps(data, ensure_ascii=False).encode() if data is not None else None
    req = Request(
        url + path,
        data=body,
        method=method,
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
    )
    with urlopen(req, timeout=15) as response:
        result = response.read()
        return result if raw else json.loads(result)


def lookup(options, pid):
    return request(options, "/service/products/" + quote(pid, safe=""))


def queue_connect(options):
    options["outbox"].parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(options["outbox"], timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("""CREATE TABLE IF NOT EXISTS deliveries(
        id INTEGER PRIMARY KEY, event_key TEXT NOT NULL UNIQUE, kind TEXT NOT NULL,
        payload TEXT NOT NULL, run_dir TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
        next_attempt REAL NOT NULL DEFAULT 0, delivered INTEGER NOT NULL DEFAULT 0,
        result TEXT, last_error TEXT NOT NULL DEFAULT '')""")
    return db


def enqueue(options, event_key, kind, payload, run_dir):
    with closing(queue_connect(options)) as db, db:
        db.execute(
            "INSERT OR IGNORE INTO deliveries(event_key,kind,payload,run_dir) VALUES(?,?,?,?)",
            (
                event_key,
                kind,
                json.dumps(payload, ensure_ascii=False),
                str(Path(run_dir).resolve()),
            ),
        )


def flush(options, limit=20, force=False):
    result = {"delivered": 0, "pending": 0, "errors": []}
    with closing(queue_connect(options)) as db:
        rows = db.execute(
            "SELECT * FROM deliveries WHERE delivered=0 AND next_attempt<=? ORDER BY id LIMIT ?",
            (float("inf") if force else time.time(), limit),
        ).fetchall()
    for row in rows:
        try:
            with closing(queue_connect(options)) as db:
                if db.execute(
                    "SELECT 1 FROM deliveries WHERE delivered=0 AND run_dir=? AND id<?",
                    (row["run_dir"], row["id"]),
                ).fetchone():
                    continue
            payload = json.loads(row["payload"])
            run = Path(row["run_dir"])
            if row["kind"] == "video":
                response = request(options, "/service/videos", "POST", payload)
                receipt = run / "database-record.json"
                temporary = receipt.with_suffix(".json.tmp-" + str(os.getpid()))
                temporary.write_text(
                    json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                os.replace(temporary, receipt)
            else:
                receipt = run / "database-record.json"
                if not receipt.is_file():
                    continue
                video_id = json.loads(receipt.read_text(encoding="utf-8"))["id"]
                current = request(options, f"/service/videos/{video_id}")
                response = request(
                    options,
                    f"/service/videos/{video_id}/qc",
                    "PATCH",
                    payload | {"version": current["version"]},
                )
            with closing(queue_connect(options)) as db, db:
                db.execute(
                    "UPDATE deliveries SET delivered=1,result=?,last_error=? WHERE id=?",
                    (json.dumps(response), "", row["id"]),
                )
            result["delivered"] += 1
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            # Never include credentials or remote response bodies in persisted errors.
            error = (
                f"HTTP {exc.code}" if isinstance(exc, HTTPError) else type(exc).__name__
            )
            delay = min(3600, 15 * (2 ** min(row["attempts"], 8)))
            with closing(queue_connect(options)) as db, db:
                db.execute(
                    "UPDATE deliveries SET attempts=attempts+1,next_attempt=?,last_error=? WHERE id=?",
                    (time.time() + delay, error, row["id"]),
                )
            result["errors"].append({"event": row["event_key"], "error": error})
    with closing(queue_connect(options)) as db:
        result["pending"] = db.execute(
            "SELECT COUNT(*) FROM deliveries WHERE delivered=0"
        ).fetchone()[0]
    return result


def qc_status(qc):
    passed = qc.get("qc", {}).get("overall_pass")
    return qc.get("status") or (
        "pass" if passed is True else "failed" if passed is False else "unknown"
    )


def queue_qc(options, run_dir, qc):
    digest = hashlib.sha256(json.dumps(qc, sort_keys=True).encode()).hexdigest()
    enqueue(
        options,
        "qc:" + str(Path(run_dir).resolve()) + ":" + digest,
        "qc",
        {"qc": qc, "status": qc_status(qc)},
        run_dir,
    )


def record_generation(
    options, run_dir, artifact, identity, publication=None, publication_error=""
):
    run = Path(run_dir).resolve()
    saved_payload = run / "ops-delivery.json"
    if saved_payload.is_file():
        payload = json.loads(saved_payload.read_text(encoding="utf-8"))
    else:
        if not identity.get("external_user_id"):
            raise ValueError(
                "The authenticated ComfyUI task owner is required for delivery."
            )
        product = json.loads((run / "analysis.json").read_text(encoding="utf-8"))
        manifest = json.loads(
            (run / "product/manifest.json").read_text(encoding="utf-8")
        )
        job = json.loads((run / "job.json").read_text(encoding="utf-8"))
        if manifest["pid"] != product["pid"]:
            raise ValueError("Generation and product PID do not match.")
        first = min(manifest["images"], key=lambda item: item["index"])
        photo = (run / "product" / first["file"]).resolve()
        if not photo.is_relative_to(run / "product"):
            raise ValueError("Product photo escaped its run directory.")
        photo_bytes = photo.read_bytes()
        if hashlib.sha256(photo_bytes).hexdigest() != first["sha256"]:
            raise ValueError("Product photo differs from the verified manifest.")
        qc_path = run / "qc.json"
        qc = json.loads(qc_path.read_text(encoding="utf-8")) if qc_path.exists() else {}
        qc = qc | {"status": qc_status(qc)}
        copy = read_generation_copy(run)
        values = {
            "C": product["title"],
            "G": copy["chinese"],
            "H": copy["english"],
            "I": (publication or {}).get("url") or artifact.get("oss_uri", ""),
            "J": copy["caption_english"],
            "K": " ".join(copy["hashtags"]),
        }
        payload = {
            "instance_id": options["instance_id"],
            "task_id": job["prompt_id"],
            **identity,
            "pid": product["pid"],
            "sheet": options["sheet"],
            "values": values,
            "metadata": {
                "video": artifact,
                "qc": qc,
                "publication": publication,
                "publication_error": publication_error,
                "source_url": product["source_url"],
                "photo_sha256": first["sha256"],
            },
            "photo_base64": base64.b64encode(photo_bytes).decode(),
            "photo_mime": mimetypes.guess_type(photo.name)[0] or "image/jpeg",
        }
        # This immutable envelope survives API failure and prevents retry payload drift.
        with saved_payload.open("x", encoding="utf-8") as out:
            json.dump(payload, out, ensure_ascii=False, indent=2)
    key = "video:" + payload["instance_id"] + ":" + payload["task_id"]
    enqueue(options, key, "video", payload, run)
    qc_path = run / "qc.json"
    if qc_path.exists():
        qc = json.loads(qc_path.read_text(encoding="utf-8"))
        normalized = qc | {"status": qc_status(qc)}
        if normalized != payload["metadata"].get("qc"):
            queue_qc(options, run, normalized)
    flush(options, limit=5)
    with closing(queue_connect(options)) as db:
        row = db.execute(
            "SELECT delivered,result FROM deliveries WHERE event_key=?", (key,)
        ).fetchone()
    if row["delivered"]:
        return json.loads(row["result"])
    return {
        "pending": True,
        "sheet": payload["sheet"],
        "sequence": "待投递",
        "task_id": payload["task_id"],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Retry TikTok API deliveries without regenerating videos."
    )
    parser.add_argument("command", choices=["retry", "status"])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    config = json.loads((ROOT / "config.local.json").read_text(encoding="utf-8"))
    options = settings(config)
    if not options["enabled"]:
        print(json.dumps({"enabled": False}))
        return
    if args.command == "retry":
        print(json.dumps(flush(options, force=args.force), ensure_ascii=False))
    else:
        with closing(queue_connect(options)) as db:
            print(
                json.dumps(
                    [
                        dict(r)
                        for r in db.execute(
                            "SELECT id,kind,attempts,next_attempt,delivered,last_error FROM deliveries ORDER BY id DESC LIMIT 100"
                        )
                    ]
                )
            )


if __name__ == "__main__":
    main()
