# Step 7A Branch Checklist

Recommended files to commit:

```text
ral_step7a/README.md
ral_step7a/WORKFLOW.md
ral_step7a/PAPER_INSIGHTS.md
ral_step7a/COMPARISON_INDEX.md
ral_step7a/BRANCH_CHECKLIST.md
ral_step7a/env.example
ral_step7a/launch/
ral_step7a/scripts/
ral_step7a/rviz/
ral_step7a/runs/README.md
ral_step7a/runs/.gitignore
```

Recommended lightweight run artifacts to commit if the team wants analysis
outputs in the branch:

```text
ral_step7a/runs/*/README.md
ral_step7a/runs/*/MANIFEST.md
ral_step7a/runs/*/sgraphs_wall_plane_summary.csv
ral_step7a/runs/*/sgraphs_wall_planes.csv
ral_step7a/runs/*/plots/*.png
ral_step7a/runs/*/sgraphs_topics_metadata/metadata.yaml
ral_step7a/runs/*/sgraphs_topics/metadata.yaml
```

Do not commit:

```text
*.db3
*.mcap
*.bag
*.tar
*.tar.gz
*.zip
archive_misnamed/
```

Main files for the team to read:

```text
PAPER_INSIGHTS.md
COMPARISON_INDEX.md
runs/README.md
WORKFLOW.md
```
