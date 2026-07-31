import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

const COST_NODE_NAMES = new Set([
    "ComfyUI-LLM GPT",
    "ComfyUI-LLM Agent SDK",
]);

function getOrCreateCostWidget(node) {
    let widget = node.widgets?.find((item) => item.name === "llm_cost");
    if (widget) {
        return widget;
    }

    widget = ComfyWidgets.STRING(
        node,
        "llm_cost",
        ["STRING", { multiline: true }],
        app,
    ).widget;
    widget.inputEl.readOnly = true;
    widget.inputEl.style.border = "none";
    widget.inputEl.style.backgroundColor = "transparent";
    widget.inputEl.style.minHeight = "52px";
    widget.inputEl.style.resize = "none";
    widget.inputEl.style.overflow = "hidden";
    widget.serialize = false;
    return widget;
}

app.registerExtension({
    name: "ComfyUILLMGenerationCost",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!COST_NODE_NAMES.has(nodeData.name)) {
            return;
        }

        const originalOnExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            originalOnExecuted?.apply(this, arguments);

            const summary = message?.llm_cost?.[0];
            if (!summary) {
                return;
            }

            const widget = getOrCreateCostWidget(this);
            widget.value = summary;
            const computedSize = this.computeSize();
            this.setSize([
                Math.max(this.size[0], 360),
                Math.max(this.size[1], computedSize[1]),
            ]);
            this.setDirtyCanvas(true, true);
        };
    },
});
