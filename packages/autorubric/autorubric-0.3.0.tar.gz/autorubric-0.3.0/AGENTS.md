# Research Paper Writing Guidelines

Guidelines for writing research papers targeting venues like ACL, NeurIPS, COLM, EMNLP, and similar ML/NLP conferences.

## Core Principles

### 1. Substance Over Style
- Every sentence must convey information. Cut sentences that only "sound academic."
- Make specific, falsifiable claims. "Our method improves F1 by 4.2 points on CoNLL-03" not "Our method shows promising results."
- If you can't point to evidence for a claim, delete it or hedge appropriately.
- Do not over-emphasize the importance of the paper or over-hype the results.

### 2. Technical Precision
- Use established terminology from the field. Don't invent synonyms for common terms.
- Define notation once, use consistently. Don't switch between x, X, and **x** for the same variable.
- Develop clean, mathematically precision formalisms.
- Do not formalize obvious concepts.
- Be exact about experimental details: model sizes, hyperparameters, dataset splits, compute used.

### 3. Honest Positioning
- State limitations directly. Every method has them; hiding them damages credibility.
- Compare fairly to baselines. Use the same evaluation setup, not cherry-picked conditions.
- Distinguish your genuine contributions from incremental improvements.

---

## Phrases and Patterns to Avoid

### Banned Phrases (Strong AI Tells)
These phrases are heavily overused by language models and immediately signal AI-generated text:

| Avoid                                   | Why                  | Alternative                                       |
| --------------------------------------- | -------------------- | ------------------------------------------------- |
| "delve into"                            | Extreme AI marker    | "examine", "analyze", "study", or just cut        |
| "it's important to note that"           | Filler               | State the thing directly                          |
| "in the realm of"                       | Pompous filler       | "in" or cut entirely                              |
| "a testament to"                        | Cliché               | Describe the evidence directly                    |
| "paramount"                             | Overused superlative | "critical", "essential", or be specific about why |
| "multifaceted"                          | Vague                | Describe the actual facets                        |
| "leveraging"                            | AI tell              | "using", "with"                                   |
| "harnessing the power of"               | Hyperbolic           | "using"                                           |
| "cutting-edge" / "state-of-the-art"     | Overused             | Cite actual SOTA numbers                          |
| "game-changer" / "revolutionize"        | Hyperbolic           | Describe actual impact                            |
| "in today's rapidly evolving landscape" | Cliché opener        | Cut entirely; start with substance                |
| "a myriad of"                           | Archaic, overused    | "many", "various"                                 |
| "tapestry"                              | AI tell              | Cut; use concrete description                     |
| "intricate"                             | Vague                | Describe the actual complexity                    |
| "nuanced"                               | Overused             | Be specific about the nuances                     |
| "holistic"                              | Vague                | Describe what's actually included                 |
| "synergy"                               | Corporate speak      | Describe the actual interaction                   |
| "seamlessly"                            | Almost never true    | Describe actual integration                       |
| "empower"                               | Corporate speak      | Be specific about capabilities                    |
| "streamline"                            | Vague                | Describe the actual simplification                |
| "unlock the potential"                  | Cliché               | Describe what becomes possible                    |
| "notably"                               | Overused transition  | Often cuttable; just state the notable thing      |
| "underscores"                           | AI tell              | "shows", "demonstrates", "indicates"              |
| "robust"                                | Overused             | Describe actual failure modes tested              |
| "comprehensive"                         | Often false          | Describe actual coverage                          |
| "spearheading"                          | Hyperbolic           | "leading", "developing"                           |
| "pivotal"                               | Overused             | "important", "key", or explain why                |
| "foster"                                | Vague                | Describe actual mechanism                         |
| "plethora"                              | Archaic, AI tell     | "many"                                            |
| "crucially"                             | Overused emphasis    | Let the content speak                             |

### Overused Transition Words
Vary your transitions. If you notice these appearing frequently, rewrite:
- "Furthermore" (especially at paragraph starts)
- "Additionally"
- "Moreover"
- "Subsequently"
- "Consequently"
- "In summary"
- "Taken together"

Better: Use logical connectors that reflect actual relationships, or restructure so the connection is implicit.

### Structural Patterns to Avoid

**Mechanical enumeration:**
```
❌ "First, we... Second, we... Third, we... Finally, we..."
```
Vary structure. Use enumeration sparingly for genuinely parallel items.

**Echo structure:**
```
❌ "We propose X. X is a method that... X works by..."
```
Real writing has varied sentence openings.

**The AI paragraph template:**
```
❌ [Topic sentence]. [Elaboration]. [Example]. [Implication]. [Transition to next paragraph].
```
Not every paragraph needs all components. Some should be two sentences. Some can be longer.

**Excessive hedging:**
```
❌ "This may potentially suggest that it could possibly be the case that..."
```
Take positions. Use single hedges when appropriate: "Results suggest X" is fine.

**The self-summary trap:**
```
❌ "In this section, we will discuss X. X is... [content about X]. In summary, we have discussed X."
```
Cut the framing. Just discuss X.

---

## Writing Style Guidelines

### Sentence Level

1. **Vary sentence length.** Mix short declarative sentences with longer technical ones. A paragraph of uniformly complex sentences reads as AI-generated. Make sure the sentences have a rhythm to them.

2. **Prefer active voice** for clarity, but passive is fine when the agent is irrelevant: "The model was trained for 100 epochs" is natural.

3. **Be direct.** "We use attention" not "Attention is utilized by our approach."

4. **Cut weasel words.** "very", "really", "quite", "somewhat" rarely add meaning.

5. **Contractions are acceptable** in moderation, especially in introductions. "We don't observe this effect" is fine.

### Paragraph Level

1. **Lead with the point.** The first sentence should usually state what the paragraph establishes, not build up to it.

2. **One idea per paragraph.** If you're covering two distinct points, split.

3. **Vary paragraph length.** A mix of 2-sentence and 6-sentence paragraphs is natural. Uniform length is a tell.

4. **Not every paragraph needs a transition.** Sometimes the next paragraph just... starts.

### Section Level

1. **Introduction:** Motivate with a concrete problem, not abstract importance claims. Show, don't tell, why the problem matters.

2. **Related Work:** Engage critically. Don't just summarize; explain how prior work relates to yours. "X proposed Y; we extend this by Z" or "Unlike X, we do not assume..."

3. **Methods:** Be complete enough for reproduction. Use examples. A running example through the section helps readers.

4. **Experiments:** Describe setup before results. Be specific about baselines, splits, metrics.

5. **Results:** Lead with main findings. Save caveats and analysis for after the core results.

6. **Analysis/Discussion:** This is where author voice matters. Interpret results, discuss failures, speculate (carefully) about implications.

7. **Conclusion:** Brief. Don't just summarize—indicate what's next or what remains open.

---

## Content Guidelines

### Making Claims

**Grounded claims:** Every empirical claim needs a citation or experimental evidence in your paper.
```
❌ "Recent advances have significantly improved performance."
✓ "Since BERT (Devlin et al., 2019), pretrained models have improved CoNLL-03 NER F1 from 91.0 to 94.6 (Wang et al., 2021)."
```

**Appropriate confidence:** Match claim strength to evidence.
```
❌ "Our method is superior to all existing approaches."
✓ "Our method outperforms the baselines we tested on datasets X and Y."
```

**Honest limitations:** Dedicate space to what doesn't work.
```
✓ "On low-resource languages, our method underperforms the baseline by 2.1 F1, likely because..."
```

### Technical Writing

**Notation:** Introduce all symbols before use. Use consistent conventions (bold for vectors, capitals for matrices).

**Equations:** Every equation should be referenced in text. Don't drop equations without context.

**Figures:** Make figures self-contained with complete captions. Reference all figures in text.

**Tables:** Align numbers on decimal points. Bold best results. Include standard deviations for stochastic methods.

### Citations

**Cite specifically:** "(Smith et al., 2023)" is less useful than "(Smith et al., 2023, Section 4.2)" when referring to specific ideas.

**Don't over-cite:** Citing 10 papers for a common technique looks insecure. One or two foundational references suffice.

**Engage with citations:** Don't just list names. Say what the cited work does and how it relates.

---

## Checklist Before Submission

### Authenticity Check
- [ ] Search for banned phrases listed above; remove all instances
- [ ] Read introduction aloud. Does it sound like a human wrote it?
- [ ] Check paragraph starts: excessive "Furthermore/Additionally/Moreover"?
- [ ] Verify sentence length varies (not all 20-25 words)
- [ ] Confirm specific numbers and citations back up claims

### Technical Check
- [ ] All notation defined before use
- [ ] All figures/tables referenced in text
- [ ] Experimental setup complete enough for reproduction
- [ ] Baselines fairly described and compared
- [ ] Limitations explicitly discussed

### Style Check
- [ ] No empty superlatives ("significant", "remarkable") without evidence
- [ ] Varied transitions between paragraphs
- [ ] Mix of active/passive voice
- [ ] Author voice present, especially in discussion

---

## Examples of Good vs. AI-Sounding Writing

### Introduction Opening

**AI-sounding:**
> In the rapidly evolving landscape of natural language processing, understanding context has become paramount. Recent advances have revolutionized how we approach this multifaceted challenge, leveraging cutting-edge neural architectures to unlock unprecedented capabilities.

**Better:**
> Contextual word representations have driven NLP progress for half a decade, yet most models still struggle with discourse-level phenomena. A pronoun in paragraph three may refer to an entity introduced in paragraph one—a challenge that single-sentence encoders cannot address.

### Describing a Method

**AI-sounding:**
> Our comprehensive framework holistically integrates multiple modalities, seamlessly combining textual and visual information to achieve robust multimodal understanding. This synergistic approach empowers the model to leverage complementary signals.

**Better:**
> We concatenate CLIP image embeddings with BERT text embeddings and pass both through a 2-layer transformer. This simple fusion lets the model attend across modalities without modality-specific architectural choices.

### Discussing Results

**AI-sounding:**
> The results underscore the remarkable effectiveness of our approach. Notably, we observe substantial improvements across all metrics, demonstrating the pivotal role of our proposed modifications in achieving superior performance.

**Better:**
> On SQuAD 2.0, our model improves exact match by 2.4 points over the baseline (Table 2). The gain comes primarily from unanswerable questions (+4.1), where the calibration loss prevents overconfident predictions. On answerable questions, performance is comparable (+0.8).

---

## Final Note

Good research writing has a voice. It makes choices. It takes positions. It admits uncertainty. Bland, hedged, symmetrical prose with every claim carefully balanced against a counter-claim is not "careful"—it's evasive.

Write like you're explaining your work to a smart colleague who is skeptical but fair. Be direct about what you did, honest about what worked, and clear about what you don't know.

## Directory Structure
- `AGENTS.md`: This file.
- `paper/`: Directory containing the paper's LaTeX source code.
```
paper/
├── colm2026_conference.bst
├── colm2026_conference.sty
├── experiments/ # Directory containing the paper's experiments.
├── fancyhdr.sty
├── related_work/ # Directory containing the paper's related work.
├── figures/ # Directory containing the paper's figures.
├── main.bbl
├── main.bib
├── main.tex
├── Makefile
├── math_commands.tex
└── natbib.sty
```

## Commands
- `make build`: Compile the paper.
- `make clean`: Clean the paper's compiled files.