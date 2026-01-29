# TaoCore RFC-4

## `taocore-human`: Image & Video Pipelines for Human Behavior and Emotion Signals (Using TaoCore)

**Status:** Draft
**Intended use:** Design + implementation context (Codex / Claude Code)
**Scope:** `taocore-human` (domain package) + integration boundary with `taocore`
**Primary goal:** Process photos/videos into **interpretable, bounded claims** about behavior/emotion *signals* and interaction dynamics, using TaoCore's graph/state/metrics/equilibrium/decider framework.

---

## 0. Background and motivation

Images and videos contain rich information about human behavior: movement, attention, interaction patterns, facial expressions, posture, proximity, turn-taking, and context. ML models can extract features (faces, landmarks, pose, gaze, audio sentiment), but the outputs are:

* noisy and inconsistent over frames
* probabilistic and sometimes biased
* heavily context-dependent
* easy to over-interpret ("this person is angry")

**This RFC's stance:** we do **not** claim to infer "human nature" as truth.
Instead, we build a system that produces:

* structured representations (nodes/edges/state)
* interpretable metrics (balance/flow/hubs/clusters)
* stabilized interpretations (equilibrium)
* explicit, responsible policy decisions (deciders)
* clear uncertainty and limitations

TaoCore becomes the "reasoning substrate" above feature extraction.

---

## 1. Non-goals and safety boundaries

### 1.1 Non-goals

This system does **not** aim to:

* diagnose mental health or medical conditions
* produce definitive judgments about personality or intent
* identify people unless explicitly configured and ethically justified
* act as a lie detector or "truth machine"
* replace human interpretation in sensitive contexts

### 1.2 Output discipline (bounded claims)

Outputs must be framed as:

* "signals" (probabilistic indicators)
* "patterns" (observed tendencies)
* "uncertainty-aware summaries"
* "hypotheses to review," not verdicts

---

## 2. Architecture overview

`taocore-human` is an adapter + pipeline layer that transforms real-world media into TaoCore objects:

* **Media** → feature extraction → **Nodes/Edges** → **Graph(s)**
* **Graph(s)** → metrics → equilibrium → decider → reports

Key principle:

* `taocore-human` may depend on heavy libraries/models
* `taocore` remains clean, abstract, dependency-light

---

## 3. Core data model in `taocore-human`

### 3.1 Entities (what becomes a Node)

We represent different "levels" of analysis as nodes. Common types:

1. **PersonNode**
   Represents a tracked individual across time.

* aggregated features across frames/windows

2. **FrameNode / WindowNode**
   Represents a time slice or segment.

* features summarize the scene or group state

3. **ContextNode** (optional)
   Represents scene context: location type, lighting, camera motion, etc.

**Important:** even though these are "typed" in `taocore-human`, they still map into `taocore.Node` with `features: Dict[str, float]`.

### 3.2 Relationships (what becomes an Edge)

Edges represent interactions or relationships such as:

* co-presence (same frame/window)
* proximity (distance-based)
* attention alignment (gaze/face orientation similarity)
* turn-taking / speaking order (audio-based)
* emotional contagion hypothesis (signal correlation with time lag)

Edge weights should be **interpretable** (frequency/intensity/confidence).

---

## 4. Feature extraction (models are pluggable)

### 4.1 Feature extraction is not TaoCore

Models produce features; TaoCore reasons over them.

Feature extractors must expose:

* raw outputs
* confidence scores
* failure modes (no face detected, occlusion, etc.)

### 4.2 Recommended feature families (not mandatory)

**A) Face / expression signals**

* face detection confidence
* landmarks-derived metrics (eye openness, smile intensity proxies)
* expression probabilities (if using a model), always with confidence

**B) Body / pose signals**

* keypoints
* posture openness/closedness proxies
* movement energy proxies

**C) Attention / gaze proxies**

* head orientation
* face orientation (not "true gaze" unless robust)

**D) Audio / speech signals (video)**

* speech activity (who speaks when)
* turn-taking stats
* prosody features (energy, pitch variance)
* sentiment/emotion signals only as weak indicators

**E) Scene/context signals**

* camera motion level
* illumination
* crowd density
* environmental cues (if available)

### 4.3 Identity and tracking

Tracking is often needed for video:

* assign stable track IDs
* handle occlusions and re-entry
* store track confidence

**Privacy-first default:** treat identities as anonymous track IDs unless explicitly configured.

---

## 5. Graph construction

### 5.1 Temporal representation strategy

Two core patterns:

**Pattern 1: Sequence of graphs (time-sliced)**

* each window produces a graph snapshot
* flow computed across snapshots
* equilibrium computed per node or system across time

**Pattern 2: Single aggregated graph**

* one graph for the whole clip/folder
* nodes represent people and segments
* edges encode co-occurrence and influence summaries

Both patterns are supported; choose by use case.

---

### 5.2 Node feature aggregation

For each PersonNode:

* aggregate frame/window features into stable summaries:

  * mean, median, variance
  * percentiles
  * "time-in-state" proportions
* attach uncertainty:

  * detection coverage ratio
  * average confidence
  * missingness stats

### 5.3 Edge construction rules

Edges should be created from explicit, auditable rules:

* if two persons co-occur > N windows → add edge
* if proximity below threshold frequently → increase weight
* if speech turns alternate frequently → add reciprocal interaction edges

---

## 6. Metrics applied to media graphs (using `taocore`)

### 6.1 Balance (bounded stability)

BalanceMetrics should measure:

* extremity of signals (avoid saturation)
* volatility (frame-to-frame jitter)
* uncertainty levels (confidence too low)
* coverage (too many missing detections)

Example interpretations:

* low balance may mean: "signals are unstable/insufficient to interpret"

### 6.2 Flow (directional dynamics)

FlowMetrics may measure:

* group mood drift over time
* person-level state trajectory smoothness
* directional influence proxies (lagged correlations + speaking order)

Flow is not "truth." It's a structured way to describe movement.

### 6.3 Clusters (community structure)

Clusters may represent:

* friend groups / subgroups (structurally)
* repeated co-occurrence patterns
* interaction communities

### 6.4 Hubs (structural influence)

Hubs may represent:

* central connectors across groups
* attention magnets (many ties)
* "bridge" individuals (high betweenness)

Hub ≠ "leader" by default. It's structural importance, not a moral claim.

---

## 7. Equilibrium in media interpretation

### 7.1 Why equilibrium matters here

Frame-level emotion/behavior signals oscillate. Equilibrium enables:

* stabilized per-person "state summary"
* stable group-level patterns
* explicit detection of non-convergence (ambiguity)

### 7.2 Update rule patterns (examples)

Update rules might:

* smooth node state using neighbors weighted by interaction strength
* damp extremes using balance penalties
* reduce confidence when coverage is low
* incorporate decay so older frames matter less

### 7.3 Outcomes

Solver outputs must include:

* converged equilibrium state (if any)
* diagnostics: oscillation/divergence/slow convergence
* residual history

Non-convergence is meaningful:

* signals conflict
* the clip contains mixed/rapidly changing dynamics
* the system should report ambiguity, not force a label

---

## 8. Deciders (policy layer) for responsible interpretation

Deciders convert metrics + diagnostics into actions like:

* "accept / caution / reject interpretation"
* "flag segment for review"
* "highlight top hubs"
* "report ambiguous due to oscillation"

Deciders must be:

* explicit, inspectable policies
* conservative by default for human/emotion inference

**Example policies:**

* If face coverage < X% → do not interpret expression signals
* If solver oscillates → label segment as "mixed/ambiguous"
* If confidence low → output only structural metrics (clusters/hubs), not emotional summaries

---

## 9. Output formats: reports and artifacts

`taocore-human` should output:

### 9.1 Machine-readable outputs

* graphs (nodes/edges/features)
* time-series summaries
* metric values + diagnostics
* equilibrium states

### 9.2 Human-readable summaries (carefully phrased)

* "Observed signals suggest…"
* "This segment shows increased arousal proxy…"
* "System did not converge; interpretation ambiguous…"
* "Structural hub detected (high betweenness)…"

Avoid definitive emotional labeling unless confidence + context justify it.

---

## 10. Ethics, privacy, and bias requirements (hard requirements)

1. **Data minimization**

* store only features needed for analysis
* avoid storing raw frames unless necessary

2. **Identity safety**

* default to anonymous track IDs
* optional identity mapping must be explicit and user-controlled

3. **Uncertainty always**

* every major signal must carry confidence/coverage

4. **Bias disclosure**

* document model limitations
* avoid cross-demographic overconfidence claims

5. **No high-stakes use**

* explicitly discourage medical/legal/employment surveillance uses

---

## 11. v0 implementation plan (minimal but real)

### 11.1 v0 pipeline: "Folder → Graph → Report"

**Inputs**

* folder of images OR a single short video

**Steps**

1. extract basic features (start simple; can be mocked)
2. build PersonNodes (or image-level nodes if no tracking)
3. build edges (co-occurrence/proximity if video)
4. run TaoCore metrics:

   * balance
   * clusters
   * hubs
   * simple flow (if temporal)
5. run equilibrium solver for stabilized summary
6. apply conservative decider rules
7. output JSON + a short text summary

### 11.2 v0 success criteria

* end-to-end works on local media
* outputs are interpretable and uncertainty-aware
* stable boundaries: `taocore` has no heavy deps
* non-convergence is handled and reported

---

## 12. Summary

RFC-4 defines `taocore-human` as a responsible, uncertainty-aware media pipeline layer that:

* extracts features from photos/videos using pluggable models
* maps them into TaoCore graphs/state vectors
* applies TaoCore metrics (balance/flow/clusters/hubs)
* stabilizes interpretations via equilibrium solvers
* uses explicit deciders to avoid overclaiming
* outputs both machine-readable artifacts and cautious summaries

This enables "understanding human nature" in the practical, bounded sense:

> discovering patterns and dynamics in behavior/emotion signals, with transparency and humility.
