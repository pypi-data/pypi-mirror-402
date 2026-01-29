# taocore-human

Image & video pipelines for human behavior and emotion signals using [TaoCore](https://github.com/daidaitaotao/taocore).

## Philosophy

This package processes photos and videos into **interpretable, bounded claims** about behavior and emotion *signals*. It does **not** claim to read minds or determine truth about internal states.

**Key principles:**
- Outputs are "signals" and "patterns", not definitive judgments
- Uncertainty is always explicit
- Non-convergence is meaningful (signals may conflict)
- Conservative by default for human/emotion inference

## Installation

```bash
# Basic (stub extractors only)
pip install taocore-human

# With image support
pip install taocore-human[image]

# With video support
pip install taocore-human[video]

# With ML models (PyTorch)
pip install taocore-human[ml]
```

## Quick Start

### Photo Folder Analysis

```python
from taocore_human import PhotoFolderPipeline

# Process a folder of photos
pipeline = PhotoFolderPipeline("/path/to/photos")
result = pipeline.run()

# Check if interpretation is allowed
if result.interpretation_allowed:
    print(result.report.summary)
    print(result.report.behavioral_summary)
else:
    print("Interpretation declined:", result.rejection_reasons)
    print(result.report.structural_summary)  # Still available

# Export to JSON
print(pipeline.to_json(result))
```

### Video Interaction Analysis

```python
from taocore_human import VideoInteractionPipeline

# Process a video
pipeline = VideoInteractionPipeline("/path/to/video.mp4")
result = pipeline.run()

# Temporal patterns
print(result.temporal_patterns)

# Report
print(result.report.summary)
```

## Architecture

```
Media → Feature Extraction → Nodes/Edges → Graph(s)
                                              ↓
                            Metrics (balance/flow/clusters/hubs)
                                              ↓
                                    Equilibrium Solver
                                              ↓
                                      Decider Rules
                                              ↓
                                  Uncertainty-Aware Report
```

## What This System Does NOT Do

- Diagnose mental health or medical conditions
- Produce definitive judgments about personality or intent
- Act as a lie detector or "truth machine"
- Replace human interpretation in sensitive contexts

## Components

### Nodes
- `PersonNode` - Tracked individual with aggregated features
- `FrameNode` / `WindowNode` - Time slices for temporal analysis
- `ContextNode` - Scene context (lighting, quality, etc.)

### Extractors (Pluggable)
- `FaceExtractor` - Face detection and expression signals
- `PoseExtractor` - Body pose estimation
- `GazeExtractor` - Attention/gaze estimation
- `SceneExtractor` - Scene-level features
- `StubExtractor` - Random data for testing

### Pipelines
- `PhotoFolderPipeline` - Process folder of images
- `VideoInteractionPipeline` - Process video with temporal analysis

## Output Example

```json
{
  "interpretation_allowed": true,
  "confidence_level": "moderate",
  "num_persons_analyzed": 3,
  "summary": "Analysis of 3 individuals completed with moderate confidence. Signal patterns show convergent stability.",
  "limitations": [
    "Expression and emotion signals are probabilistic estimates, not ground truth about internal states."
  ],
  "recommendations": [
    "Findings may inform further investigation but should not be treated as definitive.",
    "Never use these signals for high-stakes decisions without human oversight."
  ]
}
```

## License

MIT
