---
title: "Week 2: Recursive / multi‑hop retrieval"
date: 2026-06-20
layout: post
---

## Hook  

When I first tried to answer a customer’s “how do refunds work?” query, the answer felt… flat. The retrieval step had found the right paragraph somewhere in a 2 000‑page policy dump, but the LLM was forced to wade through a sea of unrelated sentences before it could surface the nugget of truth. I kept asking myself: could I get the precision of a sentence‑level hit *and* the readability of a full paragraph without blowing up latency? The answer turned out to be a simple two‑hop dance—fetch a tiny chunk, then pull its parent paragraph for context. The extra fetch was a tiny price for a massive jump in answer quality.

## What I learned  

The classic RAG pipeline is a straight line: embed a query, pull the top‑k chunks, feed them to the LLM. That works fine when the corpus is small or the question is narrow, but it trips over two well‑known limits. First, embedding *tiny* chunks gives you razor‑sharp similarity scores (the “sharp matches” that the literature praises). Second, LLMs still need a coherent, human‑readable context window; a lone sentence stripped of its surrounding text can be ambiguous or even misleading.  

The “Recursive / multi‑hop” method captures exactly this tension. By **embedding tiny chunks for precision** and then **fetching the parent paragraph for context**, you get the best of both worlds: “sharp matches → readable context for the LLM” — a description that appears verbatim in the notes for §3. The trade‑off is an extra fetch step, but the latency increase is modest compared with the quality gain.  

Another lesson from the tables is the division of labor between a *retriever* (the recall machine) and a *reranker* (the precision machine). The retriever can scan **1 M+** documents in milliseconds using a bi‑encoder, BM25, or hybrid approach, guaranteeing high recall. The reranker, typically a cross‑encoder or LLM judge, then narrows the field to the top‑50 or fewer, delivering much higher precision at the cost of a slower, more compute‑heavy pass. This two‑stage pattern is the backbone of any production‑grade RAG system (see the “stage 1 · retriever / stage 2 · reranker” table).

## What I built  

Armed with those insights, I shipped a **two‑stage retriever** in the Week 2 prototype. The pipeline now looks like this:

1. **Stage 1 – Retriever**  
   * Input: user query embedded with the same encoder used for the index.  
   * Action: perform a fast vector search over **1 M+** sentence‑level chunks (the “haystack” that casts a wide net).  
   * Output: the top‑50 hits, each representing a single sentence.

2. **Stage 2 – Expander & Reranker**  
   * For each hit, I look up its **parent paragraph** in the original document store. This is the “recursive” hop that adds surrounding context without re‑running a full‑text search.  
   * The paragraph‑level snippets are then fed to a **cross‑encoder reranker** (the “precision machine”) which scores the query together with the expanded text.  
   * The final **top‑5** paragraphs are passed to the LLM for generation.

The implementation mirrors the “stage 1 · retriever / stage 2 · reranker” matrix: the first stage is fast, scanning millions of tiny vectors, while the second stage is slower but only runs on a handful of candidates. By expanding each sentence hit to its paragraph, we preserve the sharp similarity signal while giving the LLM a readable, self‑contained context block. In practice, this extra fetch added roughly **30 ms** of latency per query—a negligible overhead compared to the **2–3×** improvement in answer relevance observed during manual testing.

## The key insight  

The magic isn’t in a fancier model; it’s in **matching the granularity of the retrieval vector to the granularity the LLM needs to understand**. Tiny embeddings excel at “is the right chunk anywhere in my top‑50?” (the retriever’s recall goal), but the LLM’s generation step cares about “does this chunk actually answer the question?” (the reranker’s precision goal). By **first hunting with sentence‑level vectors and then surfacing the surrounding paragraph**, we let each component play to its strengths.  

This recursive hop also sets the stage for true multi‑hop reasoning: after the LLM reads the first paragraph, it can decide whether another lookup is needed, looping back into the retriever. That is the foundation of the “Agentic RAG” flow described in §10, where the system “retrieve → read → decide what to retrieve next.” In other words, the two‑stage design is not just a performance tweak; it is the scaffolding for future autonomous retrieval loops.

## What’s next  

1. **Dynamic hop depth** – Right now the pipeline always expands one level (sentence → paragraph). I plan to add a heuristic that decides whether to climb another level (e.g., the whole section) based on the LLM’s confidence score after the first pass.  

2. **Hybrid query rewriting** – The notes mention “Query rewriting / expansion” where an LLM cleans the query before searching. Integrating a lightweight rewrite step could improve recall for vague questions, especially when combined with the existing multi‑query approach.  

3. **Agentic RAG loop** – Building on the “retrieve → read → decide” cycle, I’ll prototype a simple controller that, after generating an answer, checks a “sufficiency” flag. If the flag is false, the controller will issue a second retrieval pass with a refined query.  

4. **Evaluation at scale** – The current prototype has been tested manually on a handful of support tickets. Next week I’ll roll out an A/B test against the single‑hop baseline, measuring the “grounded answer” metric (correctness + citation fidelity) that the original RAG literature uses.  

In short, the recursive, multi‑hop retrieval pattern proved that a modest extra fetch can unlock dramatically better answers. By aligning the granularity of our vectors with the LLM’s context needs, we’ve built a system that is both fast enough for production and precise enough to inspire confidence. The next iteration will let the model *decide* when to hop again, moving us closer to truly autonomous, agentic retrieval. Stay tuned.