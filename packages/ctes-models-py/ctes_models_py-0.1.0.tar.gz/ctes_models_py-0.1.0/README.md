## Ciphertext Ecosystem Python Models

This dependency defines the models for the ciphertext ecosystem, used for building tools that will help solve unsolved ciphers.

The model is a generated model using Protobuf.

## Usage

First, install the package with `pip install ctes-models-py`.

Example usage of the models:

```py
import ctes_models_py.model as ct

b = bytes.fromhex('aa bc de ff') # Convert hex to bytes
my_ct_encoding = ct.EncodingMetadata(encoding=ct.Encoding.BASE_CONVERSION, base=16)
my_ct_metadata = ct.CiphertextMetadata(type='', encoding=my_ct_encoding)
my_ct = ct.Ciphertext(bytes=b, metadata=my_ct_metadata)
print(my_ct) # Ciphertext bytes
print(my_ct.bytes.hex(' ')) # Ciphertext converted back to hex
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