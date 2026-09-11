# Meet Sharma — GitHub Profile Setup

## What is fixed in V3

- GitHub Stats and Most Used Languages use matching, equal-size cards.
- LeetCode uses a compact full-width local SVG card.
- The old snake is removed.
- `assets/contribution-3d.gif` is included in the package, so the heatmap is **visible immediately** after you upload the files.
- The 3D heatmap workflow then replaces that preview with the **real daily contribution calendar** from GitHub.

## 1. Copy the files

Copy the package contents into:

`https://github.com/itsmeetsharma777/itsmeetsharma777`

Keep these paths:

```text
.github/workflows/contribution-3d.yml
.github/workflows/github-stats.yml
.github/workflows/leetcode-card.yml
scripts/generate_3d_contributions.py
scripts/generate_leetcode_card.py
scripts/normalize_analytics.py
assets/contribution-3d.gif
assets/leetcode-card.svg
README.md
```

## 2. GitHub Actions permission

Repository → **Settings → Actions → General → Workflow permissions** → select **Read and write permissions** → Save.

## 3. Run the workflows

Go to **Actions** and run:

- **Update GitHub Analytics**
- **Update LeetCode Card**
- **Update 3D Contribution Heatmap**

The 3D workflow uses the GitHub GraphQL API and `GITHUB_TOKEN` to read the contribution calendar. It then writes the real data to `assets/contribution-3d.gif`.

## 4. Remove the old snake

Delete the old `Generate Contribution Snake` workflow if it is still in `.github/workflows/`.

Also remove any old README reference to:

`github-contribution-grid-snake.svg`

The README should use only:

`./assets/contribution-3d.gif`
