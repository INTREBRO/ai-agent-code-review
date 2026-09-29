# Repository context implementation plan

1. Add offline tests for file discovery, retrieval, prompt size and opt-in behavior.
2. Add bounded Python RAG modules and local JSON cache.
3. Pass retrieved context into the Python review prompt with per-file fallback.
4. Supply `REPO_NAME` and the `RAG_ENABLED` switch in the real GitHub workflow.
5. Document enablement and run offline tests plus syntax checks.
