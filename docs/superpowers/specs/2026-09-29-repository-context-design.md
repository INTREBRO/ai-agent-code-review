# Repository context foundation

The real AI review job runs `.ai-review/ai-agent-review.py`. The repository context feature therefore extends that Python path. It is opt in through `RAG_ENABLED=true`; the existing diff prompt is the default.

## Data flow

1. Discover up to 200 small, supported source and Markdown files in the checked out repository, excluding generated and hidden directories.
2. Split them into at most 400 chunks of 80 lines and 8,000 characters. Keep path and starting line for each chunk.
3. Generate embeddings with OpenAI `text-embedding-3-small` in batches and cache chunks plus vectors in `.rag-cache/index.json`. Reuse the cache only when the content digest and model match.
4. For each PR patch, embed its path and diff, rank chunks by cosine similarity, and add up to three chunks within a 6,000 character context budget.
5. Treat repository text as untrusted reference material. Any indexing or retrieval error leaves that file's review on the original diff path.

## Boundaries

`indexer.py` owns discovery, chunking and cache validity. `embeddings.py` owns the provider request. `retriever.py` owns ranking. `context_builder.py` owns prompt size. The existing reviewer owns GitHub I/O and model prompting.

This first stage uses a local JSON index to avoid adding a database service. The cache is ignored by Git. Enabling the feature sends selected repository source to the embedding API, incurs API usage, and may increase review duration. The Node.js reviewer remains a separate path.

## Validation

Offline tests cover source filtering, indexing and persistence, ranking, prompt budget, and opt-in prompt behavior. A live GitHub PR and OpenAI key are required to validate end-to-end API behavior.
