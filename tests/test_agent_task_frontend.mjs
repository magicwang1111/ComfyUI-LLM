import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

class Element {
    constructor(tag) { this.tag = tag; this.style = {}; this.children = []; }
    append(...children) { this.children.push(...children); }
    replaceChildren(...children) { this.children = children; }
    add(child) { this.children.push(child); }
}
let extension;
const calls = [];
const app = { registerExtension(value) { extension = value; } };
const api = {
    apiURL: (path) => path,
    async fetchApi(path) {
        calls.push(path);
        const id = path.split('/')[3].split('?')[0];
        return { ok: true, async json() { return {
            id, state: 'completed', children: [], events: [{ seq: 1, message: `log-${id}` }],
            result: { text: `result-${id}`, artifacts: [{ content_type: 'video/mp4', url: `/video/${id}` }] },
        }; } };
    },
};
const source = fs.readFileSync(new URL('../web/agent_task.js', import.meta.url), 'utf8')
    .replace(/^import .*;\r?\n/gm, '');
vm.runInNewContext(source, {
    app, api, document: { createElement: (tag) => new Element(tag) },
    Option: class extends Element {}, console, setTimeout, clearTimeout,
});
class Node {
    constructor(id) { this.id = id; this.size = [300, 200]; this.properties = {}; }
    addDOMWidget(name, type, element) { this.panel = element; return {}; }
}
await extension.beforeRegisterNodeDef(Node, { name: 'ComfyUI-LLM Agent Task' });
const first = new Node(1);
const second = new Node(1); // Same canvas node ID must not mix independent tasks.
first.onNodeCreated();
second.onNodeCreated();
first.onExecuted({ agent_task_id: ['task-a'] });
second.onExecuted({ agent_task_id: ['task-b'] });
await new Promise(setImmediate);
assert.equal(first.properties.agent_task_id, 'task-a');
assert.equal(second.properties.agent_task_id, 'task-b');
assert(first.panel.children.find((el) => el.tag === 'pre').textContent.includes('log-task-a'));
assert(second.panel.children.find((el) => el.tag === 'pre').textContent.includes('log-task-b'));
const restored = new Node(7);
restored.properties.agent_task_id = 'task-a';
restored.onNodeCreated();
restored.onConfigure();
await new Promise(setImmediate);
assert(restored.panel.children.find((el) => el.tag === 'pre').textContent.includes('log-task-a'));
for (const node of [first, second, restored]) node.onRemoved();
assert.equal(calls.length, 3);
console.log('Agent frontend: task isolation, saved binding and result rendering passed');
