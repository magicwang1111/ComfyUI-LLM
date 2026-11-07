"""Standalone entry point; bypasses ComfyUI plugin/node imports."""

from agent_worker import _module


if __name__ == '__main__':
    _module('orchestration.service').main()
