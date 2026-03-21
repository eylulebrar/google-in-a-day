# Production Roadmap: Scaling to High-Scale Environments

## Infrastructure & Scalability

To transition this lightweight, memory-bound search engine into a high-scale environment, the architecture must move to a distributed microservices model. The in-memory `queue.Queue` should be replaced with a persistent message broker like **Apache Kafka** or **RabbitMQ**. For managing billions of URLs, a **Redis Cluster** utilizing a **Bloom Filter** is recommended to maintain the "visited" set with O(1) time complexity and minimal memory footprint.

## Data Persistence & Storage Management

Current state persistence utilizes a monolithic `snapshot.json` file which overwrites itself on every exit. While efficient for small-scale projects, this approach faces scalability bottlenecks as the index grows (Linear Growth Complexity). In a production scenario:
- **Incremental Checkpointing:** Instead of a full memory dump, the system should implement incremental logging (Write-Ahead Logging - WAL), where only new changes are appended to the storage.
- **Search Backend:** The local `indexed_data` should be migrated to a distributed search engine like **Elasticsearch** or **Meilisearch**, which handles sharding and high-concurrency queries far more efficiently than an in-memory dictionary.
- **Stop-word Filtration:** To prevent "Relevancy Inflation" (where common words like 'the' or 'are' dominate search results), a pre-processing pipeline should be added to filter out stop-words and apply **TF-IDF** or **BM25** ranking algorithms.
- **Domain Scoping:** Future iterations should include a domain-lock feature to prevent the crawler from wandering into unrelated external domains (e.g., Zyte or Goodreads) unless explicitly whitelisted.