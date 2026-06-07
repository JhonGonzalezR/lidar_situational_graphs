# Blocked S-Graphs Step 7A Run: `walls_pillars_sgraphs_standard_optimized_old_001`

Date: 2026-06-04

## Input

```text
bags/walls_pillars-20260604T021433Z-3-001/walls_pillars/walls_pillars_0.db3
```

## Status

The workflow cannot be executed on this input because the original SQLite
rosbag is truncated.

Verified facts:

```text
available file size: 41,943,040 bytes
available SQLite pages: 10,240 pages at 4,096 bytes/page
header-declared size: 148,893 pages, approximately 610 MB
SHA256: 933f0b4cc87e657fef7d35238b4e5cb4f6f09111f19ea2933d1f37c33e38eb78
```

The `messages` table root references child pages `76113` and `76114`, both
beyond the available file. `ros2 bag reindex`, SQLite integrity checks, and
SQLite recovery therefore cannot recover any message rows. The only other copy
found locally contains the same truncated file.

No CSVs or plots were fabricated. A complete copy of the original rosbag is
required before S-Graphs can produce defensible results for this dataset.

