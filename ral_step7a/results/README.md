# RA-L Step 7A Results

This directory is deprecated for active Step 7A run outputs.

Use:

```text
../runs/
```

for both full run artifacts and lightweight derived analysis files.

Large rosbag2 `.db3` files are intentionally not versioned. They are local or
external artifacts and should be shared through a dataset/artifact channel when
needed.

Recommended shareable contents per run:

- `README.md`: run context and interpretation.
- `MANIFEST.md`: files, checksums, and provenance.
- `sgraphs_wall_planes.csv`: derived wall-plane observations.
- `plots/*.png`: diagnostic quick-look figures.
- `sgraphs_topics_metadata/metadata.yaml`: rosbag2 metadata for the recorded
  S-Graphs output bag.

Do not treat the diagnostic plots as final paper figures. They are used to
validate that S-Graphs produced stable wall-plane outputs before formal
comparison with InGraph `WallLike`.

Shareable `.tar.gz` bundles should now be stored under the corresponding
`runs/<RUN_ID>/shareable_bundle/` directory when they contain only lightweight
documentation, CSVs, plots, and metadata.
