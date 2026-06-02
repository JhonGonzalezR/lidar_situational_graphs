# Manifest: `spot_dinamicaStaticV0_sgraphs_step7a_old_002`

## Shareable Files In This Directory

| File | Purpose | SHA256 |
|---|---|---|
| `sgraphs_wall_planes.csv` | Derived plane observation table from `/s_graphs/all_map_planes`, including map-frame and odom-frame fields | `56cf79346a0bb6726ddb96d5d484d937da26357e5ef184dcd0a87afac9d14073` |
| `sgraphs_wall_plane_summary.csv` | Per-plane-ID persistence and stability summary | `529a89d833fa50a0c981f69a9e7e80f09535c52682e9eea44e13f4d8271a02f1` |
| `plots/sgraphs_wall_plane_id_counts.png` | Diagnostic plane-id observation count plot | `0f5c5ba4147ef2a6226b74612623a71b423c1344a3b28a272b45629797c65979` |
| `plots/sgraphs_wall_plane_segments_odom.png` | Diagnostic top-down wall-segment approximation by persistent plane ID | `3594ceacfe611526a26a2809d8d5ba18c3eeac36d9e1b603d06348520e3b0d27` |
| `plots/sgraphs_lidar_wall_overlay_odom.png` | Visual sanity check overlaying sampled LiDAR points and S-Graphs wall hypotheses | `fabc43daed1744688fb3e8949446accf610bcb65b4aa2ed70b219056c6d4e539` |
| `sgraphs_topics_metadata/metadata.yaml` | rosbag2 metadata for the raw S-Graphs output bag | See file-level provenance below |

## External Raw Artifact

The raw S-Graphs output rosbag is intentionally not versioned here:

```text
/tmp/ral_step7a_sgraphs_runs/spot_dinamicaStaticV0_sgraphs_step7a_old_002/sgraphs_topics/sgraphs_topics_0.db3
```

Size:

```text
935.5 MiB
```

SHA256:

```text
7518b38bfbb934dd76fce56d9c8cbed1518b74f40dfe76218bc089ba45242731
```

If this raw bag is shared with collaborators, keep the `metadata.yaml` alongside
the `.db3` file and verify the checksum before deriving metrics.

## Shareable Bundle

Created bundle:

```text
../spot_dinamicaStaticV0_sgraphs_step7a_old_002_shareable.tar.gz
```

Expected size:

```text
about 87 KiB
```

This bundle excludes the raw `.db3` bag. Its checksum is stored as a sibling
`.sha256` file outside the bundle to avoid self-referential checksum drift.

## Reproduction Commands

Run S-Graphs:

```bash
OUTPUT_ROOT=/tmp/ral_step7a_sgraphs_runs \
CONTAINER_NAME=sgraphs_step7a \
ROOM_SEGMENTATION=old \
./lidar_situational_graphs/ral_step7a/scripts/run_sgraphs_docker.sh
```

Record outputs:

```bash
RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_002 \
OUTPUT_ROOT=/tmp/ral_step7a_sgraphs_runs \
CONTAINER_NAME=sgraphs_step7a \
./lidar_situational_graphs/ral_step7a/scripts/record_sgraphs_topics.sh
```

Play input bag inside Docker:

```bash
CONTAINER_NAME=sgraphs_step7a \
RATE=1.0 \
./lidar_situational_graphs/ral_step7a/scripts/play_spot_bag_docker.sh
```

Convert to CSV:

```bash
RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_002 \
./lidar_situational_graphs/ral_step7a/scripts/convert_sgraphs_planes_to_csv_docker.sh
```

Generate plots:

```bash
RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_002 \
./lidar_situational_graphs/ral_step7a/scripts/plot_sgraphs_wall_planes.sh

RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_002 \
./lidar_situational_graphs/ral_step7a/scripts/plot_sgraphs_wall_segments.sh

RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_002 \
./lidar_situational_graphs/ral_step7a/scripts/plot_sgraphs_lidar_overlay.sh
```
