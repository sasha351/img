# img
Image conversion tool

## CLI usage

```bash
python /home/runner/work/img/img/img_cli.py \
  --input /path/to/input.png \
  --output /path/to/output.webp \
  --output-format WEBP
```

Enable background removal mode:

```bash
python /home/runner/work/img/img/img_cli.py \
  --input /path/to/input.png \
  --output /path/to/output.png \
  --remove-background
```

Validate an expected input format:

```bash
python /home/runner/work/img/img/img_cli.py \
  --input /path/to/input.png \
  --output /path/to/output.jpg \
  --input-format PNG
```

List all formats available in the current Pillow installation:

```bash
python /home/runner/work/img/img/img_cli.py --list-formats
```

A terminal progress bar is shown while processing.

## Dependencies

```bash
pip install -r /home/runner/work/img/img/requirements.txt
```
