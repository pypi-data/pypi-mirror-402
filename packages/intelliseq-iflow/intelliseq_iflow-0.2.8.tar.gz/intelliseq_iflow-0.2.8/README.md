# intelliseq-iflow

CLI tool for iFlow - genomic data management and workflow execution.

## Installation

```bash
pip install intelliseq-iflow
```

## Usage

### Authentication

Login using OAuth Device Flow:

```bash
iflow login
```

This will open a browser for authentication. Your credentials are stored securely in your system keyring.

Check login status:

```bash
iflow status
```

Logout:

```bash
iflow logout
```

### File Operations

List files in a project:

```bash
iflow files ls --project PROJECT_ID
iflow files ls --project PROJECT_ID --path data/raw/
```

Download a file:

```bash
iflow files download --project PROJECT_ID --path data/file.txt
iflow files download --project PROJECT_ID --path data/file.txt -o local_file.txt
```

Upload a file:

```bash
iflow files upload --project PROJECT_ID local_file.txt data/uploaded.txt
```

### Running Pipelines

Submit a pipeline run:

```bash
iflow runs submit --pipeline hereditary-mock \
  -P case_id=patient-001 \
  -P child_fastq=data/R1.fastq.gz \
  --watch
```

With LIS callback:

```bash
iflow runs submit --pipeline hereditary-panel \
  -P vcf_file=data/sample.vcf.gz \
  --callback-url https://lis.example.com/api/callback
```

## Configuration

Configure environment:

```bash
iflow config env dev    # Development
iflow config env stg    # Staging
iflow config env prod   # Production
```

Select default project:

```bash
iflow config select-project
```

View current configuration:

```bash
iflow config show
```

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
ruff format .
ruff check --fix .
```
