import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "ComfyUI-LLM.QwenInputs",
    loadedGraphNode(node) {
        if (node.type !== "ComfyUI-LLM Qwen") return;
        // Saved workflows can restore sockets removed from the Python definition.
        for (let i = (node.inputs?.length ?? 0) - 1; i >= 0; i--) {
            if (["video", "video_frames"].includes(node.inputs[i].name)) {
                node.removeInput(i);
            }
        }
        if (node.widgets) {
            node.widgets = node.widgets.filter((widget) => widget.name !== "video_frames");
        }
    },
});
