from aibenchmark.providers import ollama, openrouter, nvidia, groq, zhipu

PROVIDERS = {
    "ollama": {
        "module": ollama,
        # 2026-10-30: ollama slot switched from the LOCAL model to an
        # OLLAMA CLOUD model, at Dipesh's instruction ("use cloud
        # model in ollama"). The local model (hhao/qwen2.5-coder-
        # tools:3b) was the run's wall-time bottleneck: ~1201s of run
        # 20's 1230s wall time, at ~10 tok/s on his dual-core CPU.
        # FIRST PICK (v1, DEAD): qwen3-coder:480b-cloud — the live
        # Ollama API returned 410 "qwen3-coder:480b was retired on
        # July 15, 2026" when the test script tried it (2026-10-30
        # 00:25 IST). Web sources listing it were stale; the live
        # error is authoritative. Do NOT use qwen3-coder:480b-cloud.
        # CURRENT PICK (v2): gemma4:31b-cloud — the model Ollama's
        # own 410 error message recommended ("Try gemma4:31b-cloud,
        # which is in the Free plan"), and it was already present in
        # his /api/tags list. It is a 31B-class cloud model: far
        # faster than the local 3B, but NOT a frontier coder like
        # the retired 480B flagship was — expect the slot's scores
        # to reflect a mid-size cloud model. This is a DIFFERENT
        # model from runs 11-20 (local 3B): ollama-slot scores are
        # NOT comparable across the switch; do not trend them as
        # one line.
        # Mechanics: the bench's ollama provider already posts to
        # http://localhost:11434/api/generate with the model name
        # from this registry, so NO provider code change is needed.
        # After `ollama signin` + pull, the local API routes this
        # tag to Ollama's cloud; auth is the machine's sign-in, not
        # an API key in code. (Sign-in + routing were PROVEN working
        # by the v1 test: the request reached the cloud and came
        # back with a model-specific 410, not a 401.)
        # COST: Ollama Cloud is per-token. This model is in the Free
        # plan per Ollama's own error message, which is the best
        # free-tier fit found — but Free still means a starter
        # allowance, not unlimited; check the usage page after the
        # test call. ROLLBACK: put "hhao/qwen2.5-coder-tools:3b"
        # back here; the local model stays installed.
        # JUDGE-SEPARATION NUANCE: judge is Gemini Lite and this is
        # Gemma — different models and different families (Gemma =
        # open-weights line, Gemini = frontier line), so the
        # self-grading concern does not apply. Both are Google
        # models, though: if vendor-level separation is wanted, say
        # so and a non-Google cloud tag can be tested next instead.
        "models": ["gemma4:31b-cloud"],
    },
    "openrouter": {
        "module": openrouter,
        # 2026-10-27 fix v2: meta-llama/llama-3.3-70b-instruct:free returned
        # 404 "unavailable for free", and the first replacement,
        # nvidia/nemotron-3-super-120b-a12b:free, returned the same 404.
        # cohere/north-mini-code:free returned 200 in the free-pool test
        # (2026-10-27) and served the slot through run 28. Still FREE,
        # not a paid slug.
        # 2026-11-01 SWAP (approved): slot switched to
        # nvidia/nemotron-3.5-lightning:free. Smoke PASS the same day
        # (smoke_openrouter_candidates_20261101-172600.json): HTTP 200
        # in 17,225 ms, finish_reason stop, prompt 141 / completion
        # 2158 / reasoning 1963 tokens (total ~2,300, well within the
        # 8192 cap), complete fenced code, ListNode + is_palindrome
        # interface present, functional probe 4/4 PASS. Two earlier
        # candidates failed the same gates (Flint: provider 503, no
        # upstreams; Nemotron 3 Ultra free: missing ListNode).
        # Scores from the next run on are the NEW model's only;
        # north-mini rows in runs <=28 are untouched history.
        # ROLLBACK: put "cohere/north-mini-code:free" back here.
        "models": ["nvidia/nemotron-3.5-lightning:free"],
    },
    # 2026-10-27: Hugging Face REMOVED at Dipesh's instruction — its
    # Inference Providers require paid pre-paid credits or PRO (402 "no
    # remaining credits" in the v3 test), which violates this project's
    # free-tier-only scheme. The huggingface.py file itself is left on
    # disk unused; delete it manually if you want it fully gone.
    "nvidia": {
        "module": nvidia,
        # 2026-10-27 fix: "nvidia/nemotron-3-ultra" returned 404 page not
        # found. Full current slug for Nemotron 3 Ultra on build.nvidia.com.
        "models": ["nvidia/nemotron-3-ultra-550b-a55b"],
    },
    "groq": {
        "module": groq,
        "models": ["openai/gpt-oss-120b"],
    },
    "zhipu": {
        "module": zhipu,
        # 2026-10-27: replacement for removed Hugging Face, at Dipesh's
        # instruction. Z.ai (Zhipu's international platform), model
        # glm-4.7-flash — free, coding-focused, OpenAI-compatible.
        # Judge separation holds: judge is Google Gemma, GLM is Zhipu.
        "models": ["glm-4.7-flash"],
    },
}
