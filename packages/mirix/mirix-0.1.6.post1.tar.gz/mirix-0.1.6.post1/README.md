![Mirix Logo](https://github.com/RenKoya1/MIRIX/raw/main/assets/logo.png)

## Mirix Client

Lightweight Python client for interacting with a running Mirix server.

- Website: https://mirix.io
- Documentation: https://docs.mirix.io
- Source: https://github.com/Mirix-AI/MIRIX

---

### Install

```bash
pip install mirix-client
```

### Quick Start

1) Ensure you have a Mirix server running and an API key.
2) Set your API key as an environment variable:

```bash
export MIRIX_API_KEY=your-api-key
```

3) Use the client:

```python
from mirix import MirixClient

client = MirixClient(
    api_key="your-api-key",
)

client.initialize_meta_agent(
    config={
        "llm_config": {
            "model": "gpt-4o-mini",
            "model_endpoint_type": "openai",
            "model_endpoint": "https://api.openai.com/v1",
            "context_window": 128000,
        },
        "build_embeddings_for_memory": True,
        "embedding_config": {
            "embedding_model": "text-embedding-3-small",
            "embedding_endpoint": "https://api.openai.com/v1",
            "embedding_endpoint_type": "openai",
            "embedding_dim": 1536,
        },
        "meta_agent_config": {
            "agents": [
                "core_memory_agent",
                "resource_memory_agent",
                "semantic_memory_agent",
                "episodic_memory_agent",
                "procedural_memory_agent",
                "knowledge_memory_agent",
                "reflexion_agent",
                "background_agent",
            ],
            "memory": {
                "core": [
                    {"label": "human", "value": ""},
                    {"label": "persona", "value": "I am a helpful assistant."},
                ],
                "decay": {
                    "fade_after_days": 30,
                    "expire_after_days": 90,
                },
            },
        },
    }
)

client.add(
    user_id="demo-user",
    messages=[
        {"role": "user", "content": [{"type": "text", "text": "The moon now has a president."}]},
        {"role": "assistant", "content": [{"type": "text", "text": "Noted."}]},
    ],
)

memories = client.retrieve_with_conversation(
    user_id="demo-user",
    messages=[
        {"role": "user", "content": [{"type": "text", "text": "What did we discuss on MirixDB in last 4 days?"}]},
    ],
    limit=5,
)
print(memories)
```

For more examples, see `samples/run_client.py`.

## License

Mirix is released under the Apache License 2.0. See the [LICENSE](LICENSE) file for more details.

## Contact

For questions, suggestions, or issues, please open an issue on the GitHub repository or contact us at `founders@mirix.io`.
