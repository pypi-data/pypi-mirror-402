---
hide:
  - navigation
search:
  boost: 2
---

# Matching

The matching module compares songs across different music platforms to determine if they represent the same track. It uses fuzzy string comparison via [RapidFuzz](https://github.com/maxbachmann/RapidFuzz) to handle variations in metadata between services.

## Core Concepts

### Multi-Dimensional Scoring

Rather than relying on a single metric, matching evaluates five independent dimensions:

| Dimension | Description                               |
|-----------|-------------------------------------------|
| Name      | Song name similarity                      |
| Title     | Full title (including artist) similarity  |
| Artists   | Bidirectional artist name comparison      |
| Album     | Album name similarity                     |
| Length    | Duration similarity using an easing curve |

Each dimension is scored 0-100, giving a total range of 0-500.

### Fuzzy String Matching

String comparisons use RapidFuzz's QRatio algorithm, which tolerates:

- Minor spelling differences and typos
- Capitalization and punctuation variations
- Whitespace differences
- Platform-specific formatting

### Slugification

Before comparison, both songs are "slugified" - converted to a normalized form by removing special characters, diacritics, and converting to lowercase. This improves match reliability across different platforms that may format metadata differently.

## Match Quality

The total score maps to quality thresholds via `MatchQuality`:

| Quality | Threshold | Meaning |
|---------|-----------|---------|
| `PERFECT` | 500 | Exactly the same song |
| `GREAT` | 475+ | Extremely likely the same song (minor platform discrepancies) |
| `GOOD` | 400+ | Likely a different version (e.g., live version) |
| `MEDIOCRE` | 300+ | Probably a cover or different artist's version |
| `BAD` | <300 | Not the same song |

## Workflow

The `match()` function orchestrates the comparison:

1. **Slugify** both the original and result songs
2. **Compare** each dimension:
   - Name and title use direct string comparison
   - Artists are matched bidirectionally (original→result and result→original), then averaged
   - Album defaults to 50 if the result has no album metadata
   - Length uses an easing curve for intelligent duration comparison
3. **Calculate** the total score by summing all dimension scores
4. **Determine** quality based on threshold ranges

### Length Matching

Duration comparison uses a quadratic easing curve rather than linear scaling:

\[
y = 1 - (f \cdot x^2)
\]

Where \(x\) is the normalized duration difference (0-1 scale based on a 120-second ceiling) and \(f\) is the falloff factor (default 4.8). This means small differences have minimal impact while larger differences are penalized more sharply.

## Components

- **`MatchResult`**: Dataclass holding all dimension scores with properties for calculating `sum`, `quality`, and `artists_match_avg`
- **`match(original_song, result_song)`**: Main entry point that returns a `MatchResult`
- **`MatchQuality`**: Enum defining quality thresholds

See the [reference](../reference/matching/index.md) for complete API documentation.
