# SDF-PY 🧠: Synaptic Data Format

[![PyPI version](https://badge.fury.io/py/sdf-py.svg)](https://badge.fury.io/py/sdf-py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Welcome to `sdf-py`, the official Python implementation of the **Synaptic Data Format (SDF)**.

SDF is a next-generation binary format engineered for the age of AI. It's designed from the ground up to be the nervous system for modern data pipelines, seamlessly connecting data sources, training loops, and inference engines.

## ✨ Key Features

*   🧠 **Tensor-Native:** Tensors are a first-class citizen. No more flattening or base64 encoding. `numpy` arrays are stored directly and efficiently.
*   🛤️ **Sequence-Aware:** Natively represent sequences like RL trajectories or time-series events within a single record, preserving temporal context.
*   🌊 **Streaming-First:** Built as an append-only log, SDF is perfect for real-time data streams and efficient sequential reads during model training.
*   🔒 **Schema-Driven & Self-Describing:** Files are strongly typed and contain their own schema, eliminating ambiguity and making datasets portable.
*   🛠️ **Powerful CLI:** Inspect metadata, check record counts, and peek at data directly from your terminal.

## 🚀 Installation

Install `sdf-py` directly from PyPI:

```bash
pip install sdf-py
```

## ⚡ Quickstart

Let's create, write to, and read from an `.sdf` file in under 20 lines of code.

```python
import numpy as np
import os
from sdf_py import SDFWriter, SDFReader

# 1. Define the schema for your dataset
schema = {
    "image": {"type": "tensor", "dtype": "uint8", "shape": [64, 64, 3]},
    "label": {"type": "scalar", "dtype": "int32"}
}

file_path = "my_first_dataset.sdf"

# 2. Write data using a context manager
with SDFWriter(file_path, schema=schema) as writer:
    for i in range(10):
        record = {
            "image": np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8),
            "label": i
        }
        writer.write(record)

print(f"✅ Dataset created at '{file_path}'")

# 3. Read and iterate over the data
with SDFReader(file_path) as reader:
    print("\n📖 Reading first record...")
    # The reader is an iterator
    first_record, _ = next(reader)
    
    image_tensor = first_record['image']
    label = first_record['label']
    
    print(f"Read back label: {label}")
    print(f"Read back image tensor with shape: {image_tensor.shape} and dtype: {image_tensor.dtype}")
```

## 💻 Command-Line Interface (CLI)

After installing, you get the powerful `sdf` command.

#### `sdf inspect`
Get a high-level overview of your file, including its schema and total record count.

```bash
sdf inspect my_first_dataset.sdf
```
 <!-- You can add a screenshot here -->

#### `sdf head`
Peek at the first few records in a human-readable format.

```bash
# Show the first 3 records
sdf head my_first_dataset.sdf -n 3
```
 <!-- You can add a screenshot here -->

## 🤖 Advanced Usage: RL Trajectories

SDF's native sequence support makes it ideal for RL. A single record can hold an entire episode.

```python
# Schema for an RL trajectory
rl_schema = {
    "trajectory": {
        "type": "sequence",
        "timesteps": {
            "state": {"type": "tensor", "dtype": "float32", "shape": [84, 84, 4]},
            "action": {"type": "scalar", "dtype": "int32"},
            "reward": {"type": "scalar", "dtype": "float32"},
        }
    }
}

# An entire episode is just one record
episode_trajectory = [
    {"state": state_t0, "action": action_t0, "reward": reward_t0},
    {"state": state_t1, "action": action_t1, "reward": reward_t1},
    # ... more timesteps
]

# Write it as a single entry
with SDFWriter("cartpole_episodes.sdf", schema=rl_schema) as writer:
    writer.write({"trajectory": episode_trajectory})
```

## 👨‍💻 About the Founder

The Synaptic Data Format (SDF) and its Python implementation were created by **Louati Mahdi**, a Data Engineer from Tunisia with a passion for building efficient, next-generation data systems for AI.

*   **Email:** `louatimahdi390@gmail.com`
*   **GitHub:** [https://github.com/mahdi123-tech]
*   **LinkedIn:** [https://www.linkedin.com/in/mahdi1234/]

We invite the community to explore, critique, and help build the ecosystem around the Synaptic Data Format.

## 📄 License

This project is licensed under the MIT License.