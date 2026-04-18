
AI projects written in Python often involve working with numpy arrays. Even if you don’t train your own neural network, you’ll at least be touching vector embeddings, either to support semantic search or make an LLM agent empowered with RAG. Sometimes you need to serialize them in JSON, and the standard library is not the best option for this task.

# Insights
* Redis can be used as vector database as it supports cosine similarity searches https://redis.io/docs/interact/search-and-query/search/vectors/
* https://github.com/ijl/orjson for effective JSON serialization in Python
* Redis client uses default JSON module but encoder can be overwritten with https://github.com/ijl/orjson

## Links
* https://medium.com/@koypish/right-way-to-jsonify-your-gpt-embeddings-82b76f4e5483
* https://nbviewer.org/github/mihasK/try-vector-search-on-common-db/blob/main/best_way_to_jsonify_numpy.ipynb
