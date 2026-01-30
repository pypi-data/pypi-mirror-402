# pychloride

Pyodide-compatible ctypes interface for libsodium. This is a refactored pysodium wheel designed specifically for WebAssembly environments.

## Installation

### For Pyodide/PyScript

```python
import micropip
await micropip.install("pychloride")
```

### For standard Python (if you have libsodium installed)

```bash
pip install pychloride
```

## Usage

```python
import pychloride

# Generate a keypair
pk, sk = pychloride.crypto_box_keypair()

# Sign a message
sign_pk, sign_sk = pychloride.crypto_sign_keypair()
signature = pychloride.crypto_sign_detached(b"Hello World", sign_sk)
```

## Differences from pysodium

- Bundles a WebAssembly-compiled `libsodium.so` for use in Pyodide
- Includes explicit `argtypes` definitions for ctypes WASM compatibility
- Loads libsodium from the package directory instead of system paths

## Versioning

The version follows the pattern `X.Y.Z.P` where:
- `X.Y.Z` is the upstream pysodium version
- `P` is the pychloride patch version

## Credits

Based on [pysodium](https://github.com/stef/pysodium) by Stefan Marsiske.

## License

BSD 2-Clause License (same as original pysodium). Third-party notices for the
bundled libsodium binary are in `THIRD_PARTY_LICENSES.md`.
