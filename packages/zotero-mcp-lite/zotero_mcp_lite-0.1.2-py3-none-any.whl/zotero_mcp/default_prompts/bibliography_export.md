# Bibliography Export Prompt

User request: {papers}

## Step 1: Find Papers

- If user mentions titles/topics → Use `zotero_search_items(query)`
- If user says "recent papers" → Use `zotero_get_recent()`
- If user provides item keys → Use those keys
- If unclear → Ask which papers to export

## Step 2: Export Citations

For each paper, call `zotero_get_item_metadata(key, include_bibtex=True)`.

Output for each:
1. **In-text citation**: (Author, Year)
2. **APA-style reference**: Full reference in APA format
3. **IEEE-style reference**: Full reference in IEEE format
4. **BibTeX entry**: For LaTeX users
