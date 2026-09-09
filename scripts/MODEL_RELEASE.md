# Model Release Tool

`./scripts/model_release.py` automates the single-supercombo release path:

1. Paste the model bot message.
2. The tool parses the branch, ONNX path, model name, release date, model ID, and commit SHAs.
3. It scans every listed upstream commit for `tinygrad`, `modeld`, or Chestnut runtime changes.
4. It downloads the Git LFS object without loading it into shell variables.
5. It asks for the comma IP, transfers the ONNX, and runs the device compiler.
6. It verifies the returned PKL or multipart checksum.
7. It uploads `models/<id>/`, `onnx/<id>/`, and `manifests/` to Hugging Face.
8. It pushes GitHub one artifact part per commit and the manifest last.

Run interactively:

```sh
./scripts/model_release.py
```

Paste the complete bot message, press `Ctrl-D`, then enter the comma IP. The
default runtime behavior version is `v16`; the `Model vN` line is treated as
the model iteration/name, not the runtime behavior version. Override an
ambiguous ID with `--model-id`, or the runtime contract with
`--behavior-version v15`.

For the normal model bot flow, a commit SHA alone is also accepted:

```sh
./modelgrab f877d7a0ccc3cce943c76e285214c020cd65c899
```

The tool resolves the commit's changed driving ONNX, associated pull-request
branch/title, GPU status, and commit date through GitHub. If GitHub cannot
associate a human model title with the SHA, it derives the name from the ONNX
filename; use `--model-id` when an exact local naming convention is required.

Useful non-interactive form:

```sh
./scripts/model_release.py \
  --text-file release-message.txt \
  --ip 192.168.3.110
```

The tool refuses `192.168.3.109`. It also stops before downloading or compiling
if any supplied commit changes runtime code. Review the warning first, then
rerun with `--allow-runtime-changes` only after Firestar approves it.

The default resources checkout is `~/StarPilot-Resources` on branch `Models`.
It must be clean and synchronized before starting. The default Hugging Face
bucket is `StarPilot-Driving/StarPilot-Resources`; authenticate with `hf auth login`
before use. Use `--dry-run` to test parsing and the runtime scan without
touching the device or either resource store.

Failed runs leave the source, compiled parts, logs, and result JSON in the
workspace so the cause can be inspected. A rerun requires `--force` when the
same source path already exists.
