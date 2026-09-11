# Meet Sharma — GitHub Profile Setup

## 1. Copy the files into your profile repository

Copy the contents of this package into:

`https://github.com/itsmeetsharma777/itsmeetsharma777`

Make sure these paths exist:

```text
.github/workflows/github-stats.yml
.github/workflows/contribution-3d.yml
scripts/generate_3d_contributions.py
assets/contribution-3d.gif
README.md
```

## 2. Keep GitHub Actions write permission enabled

In the repository go to:

**Settings → Actions → General → Workflow permissions**

Select **Read and write permissions**, then save.

## 3. Run the workflows

Open **Actions** and run:

- **Update GitHub Analytics**
- **Update 3D Contribution Heatmap**

Both workflows also run automatically on a schedule.

## 4. Important: remove the old snake workflow

Delete the old workflow named:

`Generate Contribution Snake`

Also remove any old README reference containing:

`github-contribution-grid-snake.svg`

The new README uses:

`./assets/contribution-3d.gif`

The generated GIF is built from GitHub's public contribution calendar for `itsmeetsharma777`, so it updates with your real contribution activity.
