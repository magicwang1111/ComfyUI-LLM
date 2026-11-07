import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const NODE = "ComfyUI-LLM Agent Task";
const BASE = "/llm/agent-tasks";
const LABELS = {
    queued: "排队中", running: "Agent 执行中", delivering: "结果交付中",
    completed: "已完成", failed: "失败", cancel_requested: "正在取消",
    cancelled: "已取消", recovery_required: "执行中断，待恢复",
};
const TERMINAL = new Set(["completed", "failed", "cancelled", "recovery_required"]);

async function request(path, options) {
    const response = await api.fetchApi(path, { cache: "no-store", ...options });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
}

function installPanel(node) {
    const panel = document.createElement("div");
    panel.style.cssText = "padding:8px;background:#171717;color:#ddd;height:350px;overflow:auto;box-sizing:border-box";
    const status = document.createElement("div");
    status.textContent = "运行工作流以提交独立 Agent 任务";
    const log = document.createElement("pre");
    log.style.cssText = "white-space:pre-wrap;font:13px/1.6 monospace";
    const results = document.createElement("div");
    const cancel = document.createElement("button");
    cancel.textContent = "取消任务";
    cancel.disabled = true;
    cancel.onclick = async () => {
        const id = node.properties?.agent_task_id;
        if (!id) return;
        try {
            await request(`${BASE}/${encodeURIComponent(id)}/cancel`, { method: "POST" });
            status.textContent = "已请求取消；已开始的视频可能继续生成，子任务状态会保留。";
        } catch (error) { status.textContent = `取消失败：${error.message}`; }
    };
    const history = document.createElement("select");
    const recover = document.createElement("button");
    recover.textContent = "恢复已有视频／交付";
    recover.hidden = true;
    recover.onclick = async () => {
        const id = node.properties?.agent_task_id;
        if (!id) return;
        try {
            await request(`${BASE}/${encodeURIComponent(id)}/recover`, { method: "POST" });
            node._bindAgentTask(id);
        } catch (error) { status.textContent = `恢复失败：${error.message}`; }
    };
    history.style.maxWidth = "100%";
    const refresh = document.createElement("button");
    refresh.textContent = "任务历史";
    refresh.onclick = async () => {
        try {
            const tasks = await request(BASE);
            history.replaceChildren(new Option("选择要查看的任务", ""));
            for (const task of tasks) {
                history.add(new Option(`${new Date(task.created * 1000).toLocaleString()} ${LABELS[task.state] || task.state} ${task.id.slice(0, 8)}`, task.id));
            }
        } catch (error) { status.textContent = `历史加载失败：${error.message}`; }
    };
    history.onchange = () => { if (history.value) node._bindAgentTask(history.value); };
    panel.append(status, cancel, recover, refresh, history, log, results);
    const widget = node.addDOMWidget("agent_task_status", "AGENT_TASK_STATUS", panel, {
        getValue: () => "", setValue: () => {},
    });
    widget.computeSize = (width) => [width, 370];
    widget.serializeValue = () => undefined;
    node.size[0] = Math.max(node.size[0], 620);
    node._bindAgentTask = (id) => {
        node.properties ||= {};
        node.properties.agent_task_id = id;
        clearTimeout(node._agentTaskTimer);
        const generation = (node._agentTaskGeneration || 0) + 1;
        node._agentTaskGeneration = generation;
        let after = 0;
        let rendered = false;
        const lines = [];
        log.textContent = "";
        results.replaceChildren();
        const poll = async () => {
            let keepPolling = true;
            try {
                const task = await request(`${BASE}/${encodeURIComponent(id)}?after=${after}`);
                if (generation !== node._agentTaskGeneration) return;
                const children = task.children.map((child) => `${child.prompt_id.slice(0, 8)}：${child.state}`).join("；");
                status.textContent = `${LABELS[task.state] || task.state}${children ? ` · 视频 ${children}` : ""}${task.error ? ` · ${task.error}` : ""}`;
                for (const event of task.events || []) {
                    if (event.seq <= after) continue;
                    after = event.seq;
                    lines.push(event.message || event.event || "");
                }
                log.textContent = lines.slice(-150).join("\n");
                const childrenActive = task.children.some((child) => ["queued", "running"].includes(child.state));
                cancel.disabled = TERMINAL.has(task.state) && !childrenActive;
                recover.hidden = !task.recoverable;
                if (task.result && !rendered) {
                    rendered = true;
                    const text = document.createElement("pre");
                    text.style.whiteSpace = "pre-wrap";
                    text.textContent = `${task.result.text || ""}\n${task.result.cost || ""}`;
                    results.append(text);
                    for (const artifact of task.result.artifacts || []) {
                        const url = api.apiURL(artifact.url);
                        if (artifact.content_type?.startsWith("video/")) {
                            const video = document.createElement("video");
                            video.src = url;
                            video.controls = true;
                            video.preload = "metadata";
                            video.style.width = "100%";
                            results.append(video);
                        } else if (artifact.content_type?.startsWith("image/")) {
                            const img = document.createElement("img");
                            img.src = url;
                            img.style.maxWidth = "100%";
                            results.append(img);
                        }
                    }
                }
                keepPolling = !TERMINAL.has(task.state) || childrenActive || task.events?.length === 200;
            } catch (error) {
                if (generation !== node._agentTaskGeneration) return;
                status.textContent = `状态连接中断，正在重连：${error.message}`;
            }
            if (keepPolling && generation === node._agentTaskGeneration) node._agentTaskTimer = setTimeout(poll, 3000);
        };
        void poll();
    };
}

app.registerExtension({
    name: "ComfyUI-LLM.AgentTask",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE) return;
        const created = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = created?.apply(this, arguments);
            installPanel(this);
            return result;
        };
        const executed = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            executed?.apply(this, arguments);
            const id = message?.agent_task_id?.[0];
            if (id) this._bindAgentTask(id);
        };
        const configured = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            const result = configured?.apply(this, arguments);
            const id = this.properties?.agent_task_id;
            if (id) this._bindAgentTask(id);
            return result;
        };
        const removed = nodeType.prototype.onRemoved;
        nodeType.prototype.onRemoved = function () {
            clearTimeout(this._agentTaskTimer);
            this._agentTaskGeneration = (this._agentTaskGeneration || 0) + 1;
            return removed?.apply(this, arguments);
        };
    },
});
