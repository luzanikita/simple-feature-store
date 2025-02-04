# simple-feature-store

## Overview

This document outlines the architecture and design decisions for the Feature Store implementation, which provides both historical and real-time feature serving capabilities for machine learning models.

## Architecture Design

### Current Implementation

Our Feature Store uses a two-layered architecture. This approach stems from the fundamentally different requirements of real-time serving versus historical analysis. Online serving demands consistent low latency and high availability, while training data preparation often involves complex queries across time periods.

#### Online Storage (Redis)
The online layer uses Redis with simple JSON storage for quick feature retrieval. Each customer's latest features are stored as a JSON string:

```
key: "{customer_id}"
value: {
    "customer_id": 1,
    "purchase_value": 100.0,
    "loyalty_score": 4.5,
    "purchase_timestamp": "2024-02-05T10:30:00"
}
```

This store serves real-time inference needs with sub-millisecond latency. When new events arrive, we update features only if the timestamp is more recent than existing data.

Pros of Redis:
- Low Latency: Sub-millisecond response times for real-time serving.
- High Throughput: Handles thousands of operations per second.
- Simple Data Model: Easy-to-use key-value storage.
- Atomic Updates: Ensures consistency for feature updates.
- Scalability: Redis Cluster supports horizontal scaling.

Cons of Redis:
- Memory-Bound: Limited by RAM, expensive for large datasets.
- No Complex Queries: Lacks support for joins, aggregations, or advanced filtering.
- No Native Versioning: Requires custom logic for feature versioning.
- Limited Analytics: Not designed for historical or analytical workloads.

#### Offline Storage (DuckDB)
The offline layer maintains complete feature history in DuckDB's columnar format. It supports SQL queries for training data preparation and historical analysis. The schema preserves all feature updates with timestamps for versioning.

How DuckDB Addresses Redis Limitations
- Memory:
    - DuckDB uses disk-based storage, making it cost-effective for large datasets.
    - Handles historical data without memory constraints.

- Complex Queries:
    - DuckDB supports full SQL, enabling complex queries, joins, and aggregations.
    - Ideal for training data preparation and historical analysis.

- Versioning:
    - DuckDB stores all feature updates with timestamps, enabling point-in-time queries.
    - Supports versioning through time-based filtering.

- Analytics:
    - DuckDB is optimized for analytical workloads, including window functions and aggregations.
    - Enables efficient batch processing for model training.

### Implementation Assumptions

Our current implementation uses sequential injection, where each event is immediately written to both Redis and DuckDB, with Redis storing only the latest feature values. While this approach is simple and ensures strong consistency, it may become a bottleneck at higher scales. 

A potential enhancement would be to implement buffered writes, where Redis temporarily stores multiple feature updates (including timestamp duplicates) before periodic synchronization with DuckDB. This buffered approach would improve write efficiency and handle higher throughput but introduces eventual consistency and requires more complex error handling. Additionally, it would increase Redis memory usage as multiple versions of features need to be stored during the buffer period. 

The trade-off between immediate consistency and improved performance, along with increased memory requirements, would need to be evaluated based on specific use case requirements and infrastructure constraints.

Known Limitations
- Current Redis implementation using JSON is not optimal for memory usage
- Simple event processing without buffering or batch updates
- Basic versioning based on timestamps only
- No feature validation (except latest timestamp) or data quality checks


### Future Improvements

#### Storage Optimization

1. Redis Optimization
   - Replace JSON storage with HSET structure for better performance
   - Enable field-level updates instead of full record replacement
   - Implement TTL for automatic data expiration (maybe it is more efficient to compute on-demand features for rare customers than storing their data permanently)

2. Offline Storage Alternatives
   - Consider Parquet + Apache Iceberg for better versioning and schema evolution
   - Evaluate Feast for production-ready feature store capabilities

### Scaling Strategy

To handle millions of feature updates:
1. Add message queue (Kafka) for event ingestion
2. Implement Redis Cluster for horizontal scaling
3. Move offline storage to distributed systems
4. Optmize caching for hot features

### Production Deployment

1. Infrastructure:
   - Containerized services with Kubernetes
   - Auto-scaling based on load (horizontal scaling is a good option for NoSQL distributed databases for online storage)
   - Regular backup procedures

2. Monitoring (Prometheus + Grafana):
   - Feature freshness metrics
   - Query latency tracking
   - Storage utilization monitoring
   - Error rate alerts

3. Additional validation:
   - Pydatnic model validations for online data
   - Great Expectations for data drift and other statistical checks in historical data

## Conclusion

The implementation provides a solid foundation for feature management while acknowledging areas for improvement. The architecture balances simplicity with functionality, offering clear paths for enhancement as requirements grow.

This solution meets the basic requirements of the test task while staying within the suggested time constraint. Future improvements can address current limitations and add production-grade features as needed.


## Experiment

Copy `.env.example` to `.env` and modify, if needed

Move `test_task_data.csv` to `data` folder next to `src`:
```
├── src/
├── data/
│   └── test_task_data.csv     # Input data file
├── .env.example 
├── .env
```


Run DBs and tests
```sh
docker compose --profile test up --build
```

Setup local env, if needed
```sh
python -m venv .venv
source .venv/bin/activate
make install
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```
Run main script to see outputs
```sh
 python src/feature_store.py
```