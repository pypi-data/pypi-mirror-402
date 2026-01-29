# C# Ciphertext Ecosystem Python Models

This dependency defines the models for the ciphertext ecosystem, used for building tools that will help solve unsolved ciphers.

## Usage

First, install the package with `pip install ctes-models-py`.

Example usage of the models:

```py
# TODO
```

## Generating the model

Requires installing the [Protoc CLI](https://protobuf.dev/installation/).

Run `. ./generate.sh` to generate the latest version of the model.

## Development

Activate virtual environment:
```
python -m venv venv
source venv/bin/activate
```

Build:
```
python3 -m pip install --upgrade build
python3 -m build
```