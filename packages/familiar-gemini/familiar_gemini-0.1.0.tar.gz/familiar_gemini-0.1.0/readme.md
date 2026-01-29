# familiar-gemini

Gemini CLI agent plugin for [familiar](https://github.com/cyberwitchery/familiar).

## installation

```bash
pip install familiar-gemini
```

## usage

Once installed, the `gemini` agent becomes available in familiar:

```bash
familiar conjure gemini python sec
familiar invoke gemini bootstrap-python myapp cli
```

## requirements

- [familiar-cli](https://github.com/cyberwitchery/familiar) >= 0.1.0
- [gemini CLI](https://github.com/google/gemini-cli) installed and in PATH
