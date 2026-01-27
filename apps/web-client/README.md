# Fake News Detector

This application helps users verify claims by cross-referencing them with trusted sources and known facts.

## Proximity Score Calculation Logic
The "Proximity Score" indicates how closely a user's input matches content from a trusted source (e.g., BBC, Reuters) when a URL is provided.

### 1. Source Extraction
- The system scans the user's text for URLs from a known list of trusted domains (`trusted_sources.json`).
- If a trusted URL is found, the system fetches the webpage content.

### 2. Smart Chunking
- To prevent score dilution (where a short claim matches poorly against a long article), the source text is split into individual **paragraphs**.
- The system compares the user's text against these specific chunks rather than the entire document.

### 3. Verification Method (Hybrid)
 The system uses a two-step approach:

#### A. LLM-Based Verification (Primary)
- If an `OPENAI_API_KEY` is available in the environment, the system uses **GPT-4o-mini**.
- It sends the relevant source paragraphs and the user's claim to the LLM.
- The LLM analyzes the semantic meaning and returns:
    - A **Score (0-100)**: Representing how well the source supports the claim.
    - **Reasoning**: A brief explanation of the verdict.

#### B. Jaccard Similarity Heuristic (Fallback)
- If no API key is present, the system falls back to a mathematical approach.
- It calculates the **Jaccard Similarity** (intersection of words / union of words) between the user's text and **each paragraph** of the source.
- The **maximum score** obtained from the best-matching paragraph is used as the Proximity Score.
- This ensures that if the claim is valid and contained in one specific paragraph, it receives a high score even if the rest of the article is unrelated.

