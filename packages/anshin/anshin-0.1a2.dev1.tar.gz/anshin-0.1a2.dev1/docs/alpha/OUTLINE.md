# Core design rules

1. "Pure plan → effectful apply"

Everything should flow like:

Inputs (TOML + pinned sources) → Evaluation → IRs (data) → Realization tree → Activation plan → Apply

Enforce boundaries, later strengthen correctness (sandboxing, provenance, rollback journaling) without rewriting the whole system.

2. Make all important things first-class IRs

To stay extensible and debuggable, represent these as structured data:

- DerivationIR: build intent (inputs, env, builder, args, declared outputs)
- StoreObjectIR: outputs placed in the store with hash identity
- ServiceSpecIR: init-agnostic service definition
- SystemTreeIR: what /etc, units, symlinks should look like
- ActivationPlanIR: ordered filesystem + command operations

IRs are the compatibility layer. Implementations can evolve freely.

3. Keep v0 honest: "best-effort reproducible"

The PoC will deliver the UX (generations, rollback, pinning, profiles) even before "hard guarantees". Don’t couple UX to the enforcement mechanism. Make enforcement a backend to swap in.

---

## The minimal kernel architecture

#### Layer A — Config & pinning
- system.toml: machine config (modules enabled, options)
- lock.toml: resolved source hashes + versions + module versions + tool version

##### Interfaces

LockResolver: takes "wants" → produces lock
Fetcher: fetches by URL → content hash verified → cached

##### Future-proofing

- Flake-like inputs(?), git refs, content-addressed mirrors, etc., without changing evaluation.

#### Layer B — Module/option system (NixOS vibe)

**"Deterministic merge + provenance early."**

##### Interfaces

- OptionSchema: types/defaults/docs
- Module: returns (schema, fragments) where fragments are config contributions + conditions
- Merger: merges fragments → FinalConfig + ProvenanceGraph

##### Key choices for Python

- Avoid “implicit recursion.” Use an explicit fixpoint engine or staged evaluation:
  - Stage 1: collect schemas
  - Stage 2: merge values
  - Stage 3: allow modules to compute derived values from FinalConfig

- Provide “lazy” values as explicit Thunk objects if needed later.

##### MVP for PoC

- deep merge + priorities (default/override/force)
- explain path.to.option showing origin chain

##### Why this scales

- can later add NixOS-like features (mkIf, mkMerge, mkDefault) as merge primitives without breaking modules.

#### Layer C — Build engine (derivations)

This is where “store identity” lives.
