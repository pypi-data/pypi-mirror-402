# Barie Facia MCP

A Model Context Protocol (MCP) server for Facia facial analysis APIs: age estimation, deepfake (liveness) detection, and face match.

## Installation

Install via `uvx` (after publishing to PyPI):

```bash
uvx barie-facia-mcp
```

Or install via pip:

```bash
pip install barie-facia-mcp
```

## Usage

Run the MCP server:

```bash
barie-facia-mcp --client-id <facia-client-id> --client-secret <facia-client-secret> --storage-dir <path-to-images>
```

### Required Arguments

- `--client-id`: Facia client ID
- `--client-secret`: Facia client secret

### Optional Arguments

- `--storage-dir`: Directory containing images (defaults to current working directory)

## Tools

- **age_estimation**: Estimate age for a single image  
  - Input: `image_name` (string)
- **deepfake_detection**: Deepfake/liveness detection for a single image  
  - Input: `image_name` (string)
- **face_match**: Compare two images (face match)  
  - Inputs: `original_image_name` (string), `matched_image_name` (string)

## Development

For build and publish instructions, see [BUILD.md](BUILD.md).

## License

MIT
