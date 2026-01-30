# pyxjustiz

<p align="center">
  <a href="https://pypi.org/project/pyxjustiz/">
    <img src="https://img.shields.io/pypi/v/pyxjustiz.svg" alt="PyPI version">
  </a>
  <a href="https://pypi.org/project/pyxjustiz/">
    <img src="https://img.shields.io/pypi/pyversions/pyxjustiz.svg" alt="Python versions">
  </a>
  <a href="https://github.com/nbdy/pyxjustiz/blob/master/LICENSE">
    <img src="https://img.shields.io/github/license/nbdy/pyxjustiz.svg" alt="License">
  </a>
  <a href="https://github.com/nbdy/pyxjustiz/actions/workflows/publish.yml">
    <img src="https://github.com/nbdy/pyxjustiz/actions/workflows/publish.yml/badge.svg" alt="Build Status">
  </a>
</p>

`pyxjustiz` provides Python dataclasses for [XJustiz](https://xjustiz.justiz.de/) XML messages, automatically generated from the official XSD schemas. It simplifies working with the complex XJustiz standard by providing a type-safe way to parse, validate, and generate compliant XML messages.

---

## 🌟 Overview

Working with the XJustiz standard can be challenging due to its complexity and the sheer volume of message types. `pyxjustiz` bridges this gap by offering a comprehensive set of Python dataclasses generated using [xsdata](https://xsdata.readthedocs.io/).

With `pyxjustiz`, you get:
- **Full IDE Support**: Enjoy autocompletion and type checking for all XJustiz message types.
- **Type Safety**: Avoid manual XML manipulation and catch errors early in the development process.
- **Ease of Use**: Focus on your business logic instead of worrying about the underlying XML structure.

## ✨ Features

- **XJustiz 3.6.0**: Currently supports the latest stable version of the XJustiz standard.
- **Automatic Model Generation**: Dataclasses are generated directly from the official XSD schemas.
- **Seamless Integration**: Designed to work perfectly with the `xsdata` parser and serializer.
- **Clean API**: Provides a natural and intuitive way to handle complex legal data structures in Python.

## 🚀 Installation

You can install `pyxjustiz` using `pip`:

```bash
pip install pyxjustiz
```

Or using `uv`:

```bash
uv add pyxjustiz
```

## 📖 Usage

Using `pyxjustiz` to handle XJustiz messages is straightforward. Here are examples of parsing and serialization.

### Parsing an XJustiz Message

```python
from xsdata.formats.dataclass.parsers import XmlParser
from xjustiz.model_gen import NachrichtReg0400003

# Initialize the XML parser
parser = XmlParser()

# Load and parse an XJustiz XML file
# For example, a Handelsregister message (NachrichtReg0400003)
message = parser.from_path("YY-XYZ_HRB_12345+SI-200109111234.xml", NachrichtReg0400003)

# Access data using native Python attributes
print(f"Successfully parsed message: {message}")
```

### Serializing back to XML

```python
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

# Configure the serializer for pretty-printed output
config = SerializerConfig(pretty_print=True)
serializer = XmlSerializer(config=config)

# Render the dataclass back into an XML string
xml_output = serializer.render(message)
```

## 🛠 Maintenance & Updates

The XJustiz standard is updated periodically (see the [official release cycle](https://xjustiz.justiz.de/index.php)). To update the models in this library when a new version is released:

1. Place the new XSD files into the `xsd/` directory.
2. Run the generation script:
   ```bash
   bash model_gen.sh
   ```
