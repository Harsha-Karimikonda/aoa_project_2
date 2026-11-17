# Analysis of Algorithms — Project 2

This project studies volunteer shift assignment through network flow and
emergency supply depot selection through Set Cover. It includes a LaTeX ACM
conference report, complete Python code, tests, seeded experiments, four plots,
and appendices with source code and an LLM-use record.

## Read and compile

The compiled report is `report/main.pdf`. The source entry point is `main.tex`.
Upload `aoa_project_2_overleaf.zip` to Overleaf and select **main.tex** as the main
document, using pdfLaTeX. All paths are relative to the project root. The ACM
class and PGFPlots are available in Overleaf's standard TeX installation.

Locally, with a TeX installation:

```sh
latexmk -pdf main.tex
```

A portable Tectonic binary was downloaded for this environment, excluded from
the submission ZIP. If present, use:

```sh
tools/tectonic --outdir report main.tex
```

## Reproduce the results

Python 3.9+; no third-party Python dependencies:

```sh
python3 -m unittest discover -s tests -v
python3 -m src.experiments
python3 -m tools.verify_results
```

The experiment regenerates `results/*.csv`, the TeX numerical summary, machine
metadata, and `report/figures/*.tex`. Recompile the report after regenerating.
It uses three instances at each of five sizes for four families, five timing
batches per instance, and 100 separate small quality cases solved exactly.
Timing varies by machine. `results/metadata.json` records the supplied run.

`assign_volunteers(limits, demands, eligibility)` uses zero-based volunteer and
shift IDs; it returns feasibility, maximum assignment cardinality, selected
pairs, and counters. Shifts must not overlap.
`greedy_depots(n, coverage)` takes communities `0..n-1` and a list of coverage
sets; it returns selected zero-based candidate IDs and counters. If infeasible,
`uncovered` lists communities that no site can serve. `exact_depots` is an
exponential small-case oracle, excluded from runtime measurements.

## Before submission

- Replace author/institution placeholders in `main.tex` (at most two authors).
- Review the modeling assumptions, both correctness proofs, and measured plots.
- **Append the full conversation export to the LLM appendix.** The agent has no
  automatic provider transcript export. `provenance/interaction_record.txt` and
  `tool_log.txt` are explicitly partial, manually assembled records. They cannot
  certify compliance with the requirement to include every exact prompt and
  intermediate generated result. Include this conversation's later messages too.
  Save the full text as `provenance/full_conversation_export.txt`; recompiling
  automatically includes it in the LLM appendix.
- Recompile after final edits. The assignment did not specify a page limit;
  the current article occupies five ACM pages including references, followed by
  appendices. The initial 6–8 page target was a provisional estimate.

Raw data are synthetic, not operational Red Cross or FEMA data. The cited
organizations motivate the real-world problems; the models are our explicit
simplifications. General coverage-table hardness does not assume a geometric
travel-distance model. No claim that worst-case runtime is proved experimentally
is made.
