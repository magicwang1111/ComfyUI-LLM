import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const PROGRESS_EVENT = "comfyui-llm-agent-progress";
const LEGACY_OUTPUTS = new Set(["output_path", "artifacts_json", "state_json"]);

function findNode(nodeId) {
    return app.graph?._nodes?.find((node) => String(node.id) === String(nodeId));
}

function removeLegacyOutputs(node) {
    for (let index = (node.outputs?.length || 0) - 1; index >= 0; index -= 1) {
        if (LEGACY_OUTPUTS.has(node.outputs[index]?.name)) {
            node.removeOutput(index);
        }
    }
    node.setDirtyCanvas?.(true, true);
}

app.registerExtension({
    name: "ComfyUI-LLM.AgentSDK",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "ComfyUI-LLM Agent SDK") {
            return;
        }

        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = originalOnNodeCreated?.apply(this, arguments);
            removeLegacyOutputs(this);
            const outputDir = this.widgets?.find((widget) => widget.name === "output_dir");
            if (outputDir) {
                outputDir.computeSize = () => [0, -4];
                outputDir.draw = () => {};
            }
            const inputPath = this.widgets?.find((widget) => widget.name === "input_path");
            if (inputPath) {
                inputPath.computeSize = () => [0, -4];
                inputPath.draw = () => {};
            }
            const publishToOss = this.widgets?.find((widget) => widget.name === "publish_to_oss");
            if (publishToOss) {
                publishToOss.computeSize = () => [0, -4];
                publishToOss.draw = () => {};
            }

            const log = document.createElement("textarea");
            log.readOnly = true;
            log.placeholder = "运行时将显示 Skill 路由、模型状态和工具调用过程";
            log.style.cssText = [
                "width:100%",
                "height:260px",
                "box-sizing:border-box",
                "resize:none",
                "padding:8px",
                "border:1px solid #555",
                "border-radius:6px",
                "background:#171717",
                "color:#ddd",
                "font:14px/1.65 monospace",
            ].join(";");
            const progressWidget = this.addDOMWidget(
                "agent_progress",
                "AGENT_PROGRESS",
                log,
                {
                    getValue: () => "",
                    setValue: () => {},
                },
            );
            progressWidget.computeSize = (width) => [width, 274];
            progressWidget.serializeValue = () => undefined;
            this.size[0] = Math.max(this.size[0], 620);
            this._agentProgressLines = [];
            this._agentProgressElement = log;
            this._appendAgentProgress = (event) => {
                if (event.event === "reset") {
                    this._agentProgressLines = [];
                }
                const message = event.message || event.event;
                const time = new Date().toLocaleTimeString("zh-CN", { hour12: false });
                this._agentProgressLines.push(`[${time}] ${message}`);
                this._agentProgressLines = this._agentProgressLines.slice(-100);
                log.value = this._agentProgressLines.join("\n");
                log.scrollTop = log.scrollHeight;
            };
            return result;
        };

        const originalOnConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            const result = originalOnConfigure?.apply(this, arguments);
            removeLegacyOutputs(this);
            return result;
        };
    },
});

api.addEventListener(PROGRESS_EVENT, ({ detail }) => {
    const node = findNode(detail?.node_id);
    node?._appendAgentProgress?.(detail);
});
