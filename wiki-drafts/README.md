# Wiki Publish Guide

The markdown pages in this directory are prepared for GitHub Wiki:

- Home.md
- Getting Started.md
- Development Guide.md
- Troubleshooting.md

## 1) Enable Wiki in GitHub

1. Open repository Settings.
2. Go to Features.
3. Enable Wiki.

If wiki is disabled, `*.wiki.git` clone URL returns "Repository not found".

## 2) Publish pages

From the project root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\publish_wiki.ps1
```

## 3) Verify links

Open the Wiki tab and check each page:

- Home -> Getting Started / Development Guide / Troubleshooting
- Getting Started -> Development Guide / Troubleshooting
- Development Guide -> Getting Started / Troubleshooting
- Troubleshooting -> Getting Started / Development Guide
