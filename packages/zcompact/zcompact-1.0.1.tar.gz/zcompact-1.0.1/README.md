# zcompact

Python wrapper for [zcompact](https://github.com/zzmarks26/Zcompact) - JSON compaction with queryable ID index.

## Requirements

The `zcompact` CLI must be installed:

```bash
brew tap zzmarks26/zcompact
brew install zcompact
```

## Installation

```bash
pip install /path/to/Zcompact/python
```

## Usage

### Create an archive from .gz files

```python
from zcompact import Archive

# Create archive with secondary index
archive = Archive.create_from_files(
    "data.jcpk",
    ["file1.json.gz", "file2.json.gz"],
    id_field="id",
    index_field="_domain_uuid"
)
```

### Open an existing archive

```python
from zcompact import Archive

archive = Archive("data.jcpk")
```

### Query by primary ID

```python
# Returns dict or None
record = archive.get("user-123")

# Raises RecordNotFoundError if not found
record = archive.get_or_raise("user-123")
```

### Query by secondary index

```python
# Get all records for a company
records = archive.query_index("company-uuid-here")

for record in records:
    print(record["name"])
```

### Search by ID prefix

```python
# Get IDs starting with "user-"
ids = archive.search("user-", limit=100)
```

### Insert/Update/Delete

```python
# Insert
archive.insert("new-id", {"id": "new-id", "name": "Alice"})

# Update
archive.update("new-id", {"id": "new-id", "name": "Alice Smith"})

# Delete
archive.delete("new-id")

# Compact to reclaim space
archive.compact()
```

### Get stats

```python
stats = archive.stats()
print(f"Records: {stats['active_records']}")
print(f"Compression ratio: {stats['compression_ratio']}x")
```

## Example: AWS S3 workflow

```python
import boto3
from zcompact import Archive

s3 = boto3.client('s3')

# Download .gz files from S3
files = []
for key in ['data/part1.json.gz', 'data/part2.json.gz']:
    local_path = f"/tmp/{key.split('/')[-1]}"
    s3.download_file('my-bucket', key, local_path)
    files.append(local_path)

# Create searchable archive
archive = Archive.create_from_files(
    "records.jcpk",
    files,
    id_field="id",
    index_field="_domain_uuid"
)

# Query
company_records = archive.query_index("some-company-uuid")
```
