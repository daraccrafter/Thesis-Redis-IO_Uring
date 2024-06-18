import pandas as pd
import matplotlib.pyplot as plt

# Data for Redis and Redis io_uring
data_redis = {
    "test": ["SET"],
    "rps": [8172.61],
    "avg_latency_ms": [5.883],
    "min_latency_ms": [1.752],
    "p50_latency_ms": [4.279],
    "p95_latency_ms": [13.935],
    "p99_latency_ms": [17.999],
    "max_latency_ms": [43.775]
}

data_redis_io_uring = {
    "test": ["SET"],
    "rps": [46834.02],
    "avg_latency_ms": [0.656],
    "min_latency_ms": [0.280],
    "p50_latency_ms": [0.631],
    "p95_latency_ms": [0.927],
    "p99_latency_ms": [1.191],
    "max_latency_ms": [31.423]
}

# Create DataFrames
df_redis = pd.DataFrame(data_redis)
df_redis_io_uring = pd.DataFrame(data_redis_io_uring)

# Combine DataFrames for comparison
df_combined = pd.concat([df_redis, df_redis_io_uring], keys=['Redis', 'Redis io_uring'])

# Bar Chart for RPS
plt.figure(figsize=(10, 6))
plt.bar(['Redis', 'Redis io_uring'], [df_redis['rps'][0], df_redis_io_uring['rps'][0]], color=['blue', 'orange'])
plt.ylabel('Requests Per Second (RPS)')
plt.title('RPS Comparison')
plt.show()

# Bar Chart for Average Latency
plt.figure(figsize=(10, 6))
plt.bar(['Redis', 'Redis io_uring'], [df_redis['avg_latency_ms'][0], df_redis_io_uring['avg_latency_ms'][0]], color=['blue', 'orange'])
plt.ylabel('Average Latency (ms)')
plt.title('Average Latency Comparison')
plt.show()

# Line Chart for Latency Percentiles
plt.figure(figsize=(10, 6))
plt.plot(['p50', 'p95', 'p99'], df_redis[['p50_latency_ms', 'p95_latency_ms', 'p99_latency_ms']].values[0], label='Redis', marker='o')
plt.plot(['p50', 'p95', 'p99'], df_redis_io_uring[['p50_latency_ms', 'p95_latency_ms', 'p99_latency_ms']].values[0], label='Redis io_uring', marker='o')
plt.ylabel('Latency (ms)')
plt.title('Latency Percentiles Comparison')
plt.legend()
plt.show()
