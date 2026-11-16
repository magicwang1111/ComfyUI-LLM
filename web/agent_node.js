import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const LEGACY_OUTPUTS = new Set(["output_path", "artifacts_json", "state_json"]);
const AGENT_NODE_NAME = "ComfyUI-LLM Agent SDK";

function skillOptionsFromNodeInfo(payload) {
    const input = payload?.[AGENT_NODE_NAME]?.input?.required?.skill_override;
    if (!Array.isArray(input)) {
        return [];
    }
    if (Array.isArray(input[0])) {
        return input[0];
    }
    if (input[0] === "COMBO" && Array.isArray(input[1]?.options)) {
        return input[1].options;
    }
    return [];
}

async function refreshSkillOptions(node) {
    const widget = node.widgets?.find((item) => item.name === "skill_override");
    if (!widget) {
        return;
    }
    const refreshId = (node._skillOptionsRefreshId || 0) + 1;
    node._skillOptionsRefreshId = refreshId;
    const response = await api.fetchApi(
        `/object_info/${encodeURIComponent(AGENT_NODE_NAME)}`,
        { cache: "no-store" },
    );
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    const options = skillOptionsFromNodeInfo(await response.json());
    if (!options.length || node._skillOptionsRefreshId !== refreshId) {
        return;
    }
    widget.options ||= {};
    widget.options.values = [...options];
    if (!options.includes(widget.value)) {
        widget.value = options[0];
        widget.callback?.(widget.value);
    }
    node.setDirtyCanvas?.(true, true);
}

function scheduleSkillOptionsRefresh(node) {
    void refreshSkillOptions(node).catch((error) => {
        console.warn("[ComfyUI-LLM] Failed to refresh Skill options:", error);
    });
}

function removeLegacyOutputs(node) {
    for (let index = (node.outputs?.length || 0) - 1; index >= 0; index -= 1) {
        if (LEGACY_OUTPUTS.has(node.outputs[index]?.name)) {
            node.removeOutput(index);
        }
    }
    if (!node.outputs?.some((output) => output.name === "video")) {
        node.addOutput("video", "VIDEO");
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
            scheduleSkillOptionsRefresh(this);
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

            return result;
        };

        const originalOnConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            const result = originalOnConfigure?.apply(this, arguments);
            removeLegacyOutputs(this);
            scheduleSkillOptionsRefresh(this);
            return result;
        };
    },
});
