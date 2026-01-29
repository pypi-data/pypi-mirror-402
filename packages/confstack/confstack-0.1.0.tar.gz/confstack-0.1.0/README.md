# Multi-Layer Configuration Architecture

> **Summary**: This document describes a multi-layer configuration system with priority order (lowest to highest): (1) in-code defaults, (2) configuration file, (3) lowercase dotted environment variables, (4) uppercase underscored environment variables, (5) command line arguments.

| Priority | Layer | Name                                        | Quick Example           |
| -------- | ----- | ------------------------------------------- | ----------------------- |
| Lowest   | 1     | In-code Defaults                            | `key_00: str = "value"` |
|          | 2     | Configuration File                          | `{"key_00": "value"}  ` |
|          | 3     | Lowercase Dotted Environment Variables      | `app_name.key_00=value` |
|          | 4     | Uppercase Underscored Environment Variables | `APP_NAME_KEY_00=value` |
| Highest  | 5     | Command Line Arguments                      | `--key_00 value       ` |

## Layer 1 : In-code Defaults

```python
import pydantic as pdt

class Config(pdt.BaseModel):
    key_00: str = "layer_01_value_00"
    key_01: str = "layer_01_value_01"

    class Key02(pdt.BaseModel):
        subkey_01: str = "layer_01_value_02_01"
        subkey_02: str = "layer_01_value_02_02"
        subkey_03: str = "layer_01_value_02_03"

    key_02: Key02 = pdt.Field(default_factory=Key02)

    class Key03(pdt.BaseModel):
        class Subkey00(pdt.BaseModel):
            subsubkey_00: str = "layer_01_value_03_00_00"

        subkey_00: Subkey00 = pdt.Field(default_factory=Subkey00)

        class Subkey01(pdt.BaseModel):
            subsubkey_00: str = "layer_01_value_03_01_00"
            subsubkey_01: str = "layer_01_value_03_01_01"

        subkey_01: Subkey01 = pdt.Field(default_factory=Subkey01)

    key_03: Key03 = pdt.Field(default_factory=Key03)
```


## Layer 2 : Configuration File

```json
{
  "key_00": "layer_02_value_00",
  "key_01": "layer_02_value_01",
  "key_02": {
    "subkey_01": "layer_02_value_02_01",
    "subkey_02": "layer_02_value_02_02",
    "subkey_03": "layer_02_value_02_03"
  },
  "key_03": {
    "subkey_00": {
      "subsubkey_00": "layer_02_value_03_00_00"
    },
    "subkey_01": {
      "subsubkey_00": "layer_02_value_03_01_00",
      "subsubkey_01": "layer_02_value_03_01_01"
    }
  }
}
```

## Layer 3 : Lowercase Dotted Environment Variables

```bash
env \
  app_name.key_00="layer_03_value_00" \
  app_name.key_01="layer_03_value_01" \
  app_name.key_02.subkey_01="layer_03_value_02_01" \
  app_name.key_02.subkey_02="layer_03_value_02_02" \
  app_name.key_02.subkey_03="layer_03_value_02_03" \
  app_name.key_03.subkey_00.subsubkey_00="layer_03_value_03_00_00" \
  app_name.key_03.subkey_01.subsubkey_00="layer_03_value_03_01_00" \
  app_name.key_03.subkey_01.subsubkey_01="layer_03_value_03_01_01" \
  path/to/app_name.exe
```

```yaml
# file_name: docker-compose.yaml
services:
  app:
    image: your_app_image
    environment:
      app_name.key_00: layer_03_value_00
      app_name.key_01: layer_03_value_01
      app_name.key_02.subkey_01: layer_03_value_02_01
      app_name.key_02.subkey_02: layer_03_value_02_02
      app_name.key_02.subkey_03: layer_03_value_02_03
      app_name.key_03.subkey_00.subsubkey_00: layer_03_value_03_00_00
      app_name.key_03.subkey_01.subsubkey_00: layer_03_value_03_01_00
      app_name.key_03.subkey_01.subsubkey_01: layer_03_value_03_01_01
    command: path/to/app_name.exe
```

## Layer 4 : Uppercase Underscored Environment Variables

```bash
APP_NAME_KEY_00="layer_04_value_00" \
APP_NAME_KEY_01="layer_04_value_01" \
APP_NAME_KEY_02_SUBKEY_01="layer_04_value_02_01" \
APP_NAME_KEY_02_SUBKEY_02="layer_04_value_02_02" \
APP_NAME_KEY_02_SUBKEY_03="layer_04_value_02_03" \
APP_NAME_KEY_03_SUBKEY_00_SUBSUBKEY_00="layer_04_value_03_00_00" \
APP_NAME_KEY_03_SUBKEY_01_SUBSUBKEY_00="layer_04_value_03_01_00" \
APP_NAME_KEY_03_SUBKEY_01_SUBSUBKEY_01="layer_04_value_03_01_01" \
path/to/app_name.exe
```

```yaml
# file_name: docker-compose.yaml
version: '3.8'
services:
  app:
    image: your_app_image
    environment:
      APP_NAME_KEY_00: layer_04_value_00
      APP_NAME_KEY_01: layer_04_value_01
      APP_NAME_KEY_02_SUBKEY_01: layer_04_value_02_01
      APP_NAME_KEY_02_SUBKEY_02: layer_04_value_02_02
      APP_NAME_KEY_02_SUBKEY_03: layer_04_value_02_03
      APP_NAME_KEY_03_SUBKEY_00_SUBSUBKEY_00: layer_04_value_03_00_00
      APP_NAME_KEY_03_SUBKEY_01_SUBSUBKEY_00: layer_04_value_03_01_00
      APP_NAME_KEY_03_SUBKEY_01_SUBSUBKEY_01: layer_04_value_03_01_01
```

## Layer 5 : Command Line Arguments

```bash
path/to/app_name.exe \
  --key_00 layer_05_value_00 \
  --key_01 layer_05_value_01 \
  --key_02.subkey_01 layer_05_value_02_01 \
  --key_02.subkey_02 layer_05_value_02_02 \
  --key_02.subkey_03 layer_05_value_02_03 \
  --key_03.subkey_00.subsubkey_00 layer_05_value_03_00_00 \
  --key_03.subkey_01.subsubkey_00 layer_05_value_03_01_00 \
  --key_03.subkey_01.subsubkey_01 layer_05_value_03_01_01
```