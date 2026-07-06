# Kafka Local Setup

This document describes the local Kafka infrastructure for Sprint 2 Task 5.1. It prepares the services required for future ingestion development only; it does not create producers, consumers, topics, Spark jobs, or pipelines.

## Architecture Diagram

```text
Zookeeper
    |
    v
Kafka Broker
    |
    v
Kafka UI
```

## Services

### Zookeeper

Zookeeper coordinates Kafka broker metadata and cluster state for this Confluent Platform based local setup. Although newer Kafka deployments can use KRaft mode, this environment intentionally uses Zookeeper because it is part of the requested local infrastructure.

### Kafka Broker

Kafka is the local message broker that future ingestion producers and consumers will use. This setup exposes one broker with two listener addresses:

- `localhost:9092` for tools and applications running directly on the host machine.
- `kafka:29092` for containers running on the Docker Compose network.

Port `29092` exists because containers cannot reliably use `localhost:9092` to reach the Kafka container. Inside Docker, `localhost` means the current container, so services such as Kafka UI must use the Docker service name `kafka` and the internal listener port.

### Kafka UI

Kafka UI provides a browser-based interface for inspecting the local Kafka cluster. It is useful for validating broker connectivity, checking cluster metadata, and later reviewing topics, partitions, and consumer groups during ingestion development.

## Ports

| Service | Host Port | Container Port | Purpose |
| --- | ---: | ---: | --- |
| Zookeeper | `2181` | `2181` | Kafka metadata coordination |
| Kafka Broker | `9092` | `9092` | Host-to-Kafka access |
| Kafka Broker | `29092` | `29092` | Docker-network Kafka access |
| Kafka UI | `8080` | `8080` | Browser UI at `http://localhost:8080` |

## Start Containers

From the project root:

```powershell
docker compose -f docker/docker-compose.kafka.yml up -d
```

## Inspect Running Containers

```powershell
docker ps
```

Expected containers:

- `zookeeper`
- `kafka`
- `kafka-ui`

## Inspect Logs

Kafka broker logs:

```powershell
docker logs kafka
```

Zookeeper logs:

```powershell
docker logs zookeeper
```

Kafka UI logs:

```powershell
docker logs kafka-ui
```

## Stop Containers

```powershell
docker compose -f docker/docker-compose.kafka.yml down
```

The general Docker Compose stop command is:

```powershell
docker compose down
```

Run it from a directory containing the compose file you want to stop, or include the `-f` flag shown above.

## Validation

### Step 1: Confirm Containers Are Running

Run:

```powershell
docker ps
```

Expected containers:

- `zookeeper`
- `kafka`
- `kafka-ui`

### Step 2: Open Kafka UI

Open:

```text
http://localhost:8080
```

Expected result:

- A cluster named `local-cluster` is visible.

### Step 3: Confirm Kafka Broker Is Reachable

Run:

```powershell
docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092
```

Expected result:

- The command returns broker API version information without connection errors.

For container-to-container connectivity, Kafka UI and future Dockerized services should use:

```text
kafka:29092
```
