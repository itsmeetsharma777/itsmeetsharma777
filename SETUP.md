# Meet Sharma — GitHub Profile Setup

## What changed in this version

- **The GIF heatmap is gone.** `assets/contribution-3d.gif` is replaced by
  `assets/contribution-3d.svg` — a pure vector graphic animated with native
  SVG/SMIL (`<animate>` / `<animateTransform>`), the same technique used by
  `readme-typing-svg` and `capsule-render`. It:
  - grows in column-by-column on load (a smooth left-to-right sweep),
  - keeps a soft glow/pulse on your highest-activity days,
  - has a continuous light "scan" sweeping across it,
  - is ~160 KB instead of a multi-frame raster GIF, so it loads instantly
    and animates at native 60fps with zero JavaScript and zero lag.
- A ready-made SVG is already committed in `assets/contribution-3d.svg` with
  placeholder data, so the heatmap is **visible and animated immediately**
  after you upload the files — the workflow then overwrites it with your
  **real daily contribution calendar** from GitHub.
- Added an animated typing tagline under the social icons
  (`readme-typing-svg`) and gradient "wave" section dividers
  (`capsule-render`) so the whole page feels alive, not just the heatmap —
  both are hosted, animated SVGs with no repo maintenance required.
- GitHub Stats and Most Used Languages still use matching, equal-size cards.
- LeetCode still uses a compact full-width local SVG card.
- The old snake is still removed.

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
assets/contribution-3d.svg
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

The 3D workflow uses the GitHub GraphQL API and `GITHUB_TOKEN` to read your
contribution calendar, then regenerates `assets/contribution-3d.svg` with
your real data (and removes any leftover `.gif` from earlier versions).

## 4. Remove the old snake

Delete the old `Generate Contribution Snake` workflow if it is still in `.github/workflows/`.

Also remove any old README reference to:

`github-contribution-grid-snake.svg`

The README should use only:

`./assets/contribution-3d.svg`

## Notes on the animated elements

- **Typing tagline** and **wave dividers** are generated on the fly by
  public, widely-used services (`readme-typing-svg.demolab.com` and
  `capsule-render.vercel.app`) — nothing to host or regenerate yourself.
  You can freely edit the `lines=`, `color=`, or `customColorList=` query
  params in the URLs to change the wording or palette.
- The heatmap SVG has no external dependencies at all — it's fully
  self-contained and safe to open directly in a browser to preview.
