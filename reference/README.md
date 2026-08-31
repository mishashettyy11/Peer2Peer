# Project Context - Mini Peer-to-Peer (P2P) File Sharing System

You are my senior software architect and development mentor.

Do **not** immediately generate the entire project. First, understand the complete project context below and use it as the foundation for all future implementation steps.

---

# Project Goal

I want to build a **Mini BitTorrent-like Peer-to-Peer File Sharing System** in **Python**.

This is a **Computer Science portfolio project** intended to demonstrate my understanding of:

* Computer Networks
* Distributed Systems
* Socket Programming
* Concurrency
* File Chunking
* Data Integrity
* System Design

This is **not** intended to be a production-ready BitTorrent clone.

The objective is to create a clean, well-architected educational implementation that I can confidently explain during software engineering interviews.

---

# Constraints

* Programming Language: Python
* Backend Framework: FastAPI (only for Tracker APIs)
* Networking: Python socket library (or asyncio sockets where appropriate)
* Frontend: Simple React dashboard (minimal)
* Database: None (or JSON files if absolutely necessary)
* Deployment: Local machine only
* Budget: Zero
* Architecture: Modular Monolith
* Version Control: Git
* Platform: Windows
* Development Environment: VS Code

---

# Project Scope

The application should simulate multiple peers running on a single computer using different localhost ports.

Example:

Tracker
localhost:8000

Peer A
localhost:8001

Peer B
localhost:8002

Peer C
localhost:8003

This simulates multiple computers communicating over a network.

---

# Core Features

## 1. Tracker Server

Responsibilities:

* Register peers
* Maintain list of connected peers
* Maintain file availability
* Return list of peers owning a requested file

The tracker never transfers files.

It only introduces peers.

---

## 2. Peer

Each peer should be able to:

* Share files
* Request files
* Upload chunks
* Download chunks
* Communicate with other peers

Each peer acts as both:

* Client
* Server

---

## 3. File Chunking

Instead of sending an entire file,

split every file into fixed-size chunks.

Example:

movie.mp4

↓

chunk_1

chunk_2

chunk_3

...

Store metadata for chunk ordering.

---

## 4. Parallel Download

If multiple peers own different chunks,

download chunks simultaneously.

Example:

Chunk 1 ← Peer A

Chunk 2 ← Peer B

Chunk 3 ← Peer C

After download,

merge chunks back into the original file.

---

## 5. SHA-256 Verification

Each chunk should have a SHA-256 hash.

After downloading,

verify integrity.

If hash mismatches,

reject that chunk.

---

## 6. Progress Display

Display

* download percentage
* completed chunks
* active peers

A simple progress bar is sufficient.

---

## 7. Clean Project Structure

The project must be modular.

Avoid placing everything inside one file.

Example structure:

tracker/

peer/

chunk_manager/

hash_manager/

dashboard/

shared/

utils/

---

# Features NOT Included

Do NOT implement:

* DHT
* Magnet Links
* NAT Traversal
* Encryption
* User Authentication
* Login
* Cloud Deployment
* Kubernetes
* Kafka
* Redis
* RabbitMQ
* MongoDB
* PostgreSQL
* Advanced BitTorrent optimizations

These are intentionally excluded to keep the project achievable.

---

# Coding Principles

Always produce:

* clean architecture
* readable code
* modular code
* meaningful class names
* comments only where necessary
* proper folder structure
* separation of concerns
* production-quality coding style

---

# Teaching Style

Assume I am learning.

Whenever implementing a feature:

1. Explain why it exists.
2. Explain the architecture.
3. Explain the workflow.
4. Then implement it.

Do not skip conceptual explanations.

---

# Implementation Strategy

Never generate the whole project at once.

Break the implementation into small milestones.

Each milestone should:

* build one feature
* be testable
* compile successfully
* not break previous work

Only move to the next milestone after the previous one is complete.

---

# End Goal

By the end of the project I should have:

* Tracker Server
* Multiple Local Peers
* Chunk-based File Transfer
* Parallel Downloads
* SHA-256 Verification
* Progress Dashboard
* Clean Folder Structure
* Well-documented GitHub Repository

The project should be something I can confidently explain in a software engineering interview, focusing on networking, distributed systems, concurrency, and file transfer concepts rather than advanced BitTorrent features.
