# How to View/Export the Solution Diagram as PNG

## Quick Methods (No Installation Required)

### Method 1: Mermaid Live Editor (Easiest)
1. Go to https://mermaid.live
2. Open `solution-diagram.mmd` in a text editor
3. Copy the entire contents
4. Paste into the Mermaid Live Editor
5. Click the "Actions" menu → "Download PNG" or "Download SVG"

### Method 2: GitHub/GitLab Preview
1. Push the `solution-diagram.mmd` file to GitHub/GitLab
2. View it in the repository - it will render automatically
3. Right-click the rendered diagram → "Save image as..."

### Method 3: VS Code Extension
1. Install the "Markdown Preview Mermaid Support" extension in VS Code
2. Create a markdown file (e.g., `diagram.md`) with:
   ```markdown
   # Solution Diagram
   
   ```mermaid
   [paste contents of solution-diagram.mmd here]
   ```
   ```
3. Open the markdown preview (Cmd+Shift+V on Mac, Ctrl+Shift+V on Windows)
4. Right-click the diagram → "Save image as..."

## Method 4: Mermaid CLI (Command Line)

### Install Mermaid CLI
```bash
npm install -g @mermaid-js/mermaid-cli
```

### Convert to PNG
```bash
cd /Users/parthapmishra/mywork/cl_10/entrust
mmdc -i solution-diagram.mmd -o solution-diagram.png -w 2400 -H 1800
```

### Convert to SVG (Scalable Vector Graphics)
```bash
mmdc -i solution-diagram.mmd -o solution-diagram.svg
```

### Convert to PDF
```bash
mmdc -i solution-diagram.mmd -o solution-diagram.pdf
```

## Method 5: Online Converters

1. **Mermaid.ink** (API-based):
   - Upload your `.mmd` file to https://mermaid.ink
   - Get a direct PNG link

2. **Kroki** (Online):
   - Go to https://kroki.io
   - Select "Mermaid" as the diagram type
   - Paste your diagram code
   - Export as PNG

## Recommended: Quick Command

If you have Node.js installed, run this one-liner:

```bash
npm install -g @mermaid-js/mermaid-cli && mmdc -i solution-diagram.mmd -o solution-diagram.png -w 2400 -H 1800
```

This will:
1. Install Mermaid CLI globally
2. Convert your diagram to PNG with high resolution (2400x1800)

## Troubleshooting

**If npm is not installed:**
- Install Node.js from https://nodejs.org
- Then use Method 4 above

**If the diagram looks cut off:**
- Increase the width/height: `-w 3000 -H 2000`

**For best quality:**
- Use SVG format for presentations (scalable, no pixelation)
- Use PNG for documents and sharing

