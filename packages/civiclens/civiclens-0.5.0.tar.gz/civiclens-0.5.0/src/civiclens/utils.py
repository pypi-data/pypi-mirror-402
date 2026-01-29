import argparse


def run_ingest(args):
    """
    Ingests documents into the vector database.

    Args:
        args: Parsed argparse arguments containing the ingest command arguments
    """
    print(f"Ingesting from {args.source} at {args.path}")
    
def add_info_cmd(subparsers):
    info = subparsers.add_parser(
        "info",
        help="Display information about CivicLens AI"
    )

    info.add_argument(
        "--short",
        "-s",
        action="store_true",
        help="Show a brief description only"
    )
    
    info.add_argument(
        "--json",
        action="store_true",
        help="Output system information in JSON format"
    )

    info.set_defaults(func=run_info)


def add_ingest_cmd(subparsers):
    """
    Adds the ingest command to the CLI.

    The ingest command ingests documents into the vector database.

    The available arguments are:
    - --source: The document source (local or s3)
    - --path: The directory path or S3 bucket URI of the documents to ingest
    - --chunk-size: The number of documents to ingest at once (default: 1000)
    """
    ingest = subparsers.add_parser(
        "ingest",
        aliases=["i"],
        help="Ingest documents into the vector database"
    )

    ingest.add_argument(
        "--source",
        "-s",
        required=True,
        choices=["local", "s3"],
        help="Document source"
    )

    ingest.add_argument(
        "--path",
        "-p",
        required=True,
        help="Directory path or S3 bucket URI"
    )

    ingest.add_argument(
        "--chunk-size",
        "-cs",
        type=int,
        default=1000
    )

    ingest.set_defaults(func=run_ingest)


def add_query_cmd(subparsers):
    """
    Adds the query command to the CLI.

    The query command generates a civic summary for a given set of
    documents.

    The available arguments are:
    - question: The question to be answered by the civic summary
    - --audience: The target audience for the civic summary
    - --top-k: The number of civic summaries to return
    - --show-sources: A boolean indicating whether to show the sources of the civic summaries
    """
    query = subparsers.add_parser(
        "query", 
        aliases=["q"],
        help="Generate a civic summary for a given question")

    query.add_argument("question", type=str)

    query.add_argument(
        "--audience",
        "-a",
        choices=["child", "teen", "executive"],
        default="teen"
    )

    query.add_argument(
        "--top-k",
        "-k",
        type=int, 
        default=5
    )
    query.add_argument(
        "--show-sources",
        "-s",
        action="store_true"
    )

    query.set_defaults(func=run_query)

# def run_eval(args):
#     """
#     Run RAG evaluation on a benchmark dataset.
#     """
#     print("\n📊 Running CivicLens RAG Evaluation")
#     print(f"Dataset: {args.dataset}")
#     print(f"Metrics: {', '.join(args.metrics)}")
#     print(f"Top-K: {args.top_k}")
#     print("-" * 60)

#     dataset = load_eval_dataset(args.dataset)

#     results = []

#     for i, record in enumerate(dataset, 1):
#         question = record["question"]
#         ground_truth = record.get("ground_truth")

#         docs = retrieve_documents(
#             query=question,
#             top_k=args.top_k
#         )

#         answer, _ = generate_answer_and_summary(
#             question=question,
#             documents=docs,
#             audience="executive"
#         )

#         metrics = evaluate_answer(
#             question=question,
#             answer=answer,
#             documents=docs,
#             ground_truth=ground_truth,
#             metrics=args.metrics
#         )

#         results.append({
#             "test_number": i,
#             "question": question,
#             "answer": answer,
#             "ground_truth": ground_truth,
#             "metrics": metrics
#         })

#         print(f"✔ Test {i} completed")

#     summary = aggregate_metrics(results)

#     print("\n📈 Evaluation Summary")
#     for k, v in summary.items():
#         print(f"{k}: {v:.4f}")

#     if args.save_results:
#         save_eval_results(results, summary, args.project)


# def add_eval_cmd(subparsers):
#     eval_cmd = subparsers.add_parser(
#         "eval",
#         help="Evaluate RAG system performance on a benchmark dataset"
#     )

#     eval_cmd.add_argument(
#         "--dataset",
#         required=True,
#         help="Path to evaluation dataset (JSON, JSONL, or CSV)"
#     )

#     eval_cmd.add_argument(
#         "--project",
#         default="civiclens_evaluation",
#         help="Evaluation project name"
#     )

#     eval_cmd.add_argument(
#         "--metrics",
#         nargs="+",
#         choices=[
#             "faithfulness",
#             "answer_relevance",
#             "context_recall",
#             "context_precision"
#         ],
#         default=[
#             "faithfulness",
#             "answer_relevance",
#             "context_recall",
#             "context_precision"
#         ],
#         help="Evaluation metrics to compute"
#     )

#     eval_cmd.add_argument(
#         "--top-k",
#         type=int,
#         default=5,
#         help="Number of retrieved documents per query"
#     )

#     eval_cmd.add_argument(
#         "--save-results",
#         action="store_true",
#         help="Save evaluation results to disk"
#     )

#     eval_cmd.set_defaults(func=run_eval)


def retrieve_documents(query: str, top_k: int):
    """
    Retrieve top-k documents from the vector store.
    """
    # Example: vector_db.similarity_search(query, k=top_k)
    return "Retrieved Documents"

def generate_answer_and_summary(question="who is the president", documents="hello world", audience="youth"):
    """
    Generate a grounded answer and summary using retrieved documents.
    """
    # context = "\n\n".join(doc.page_content for doc in documents)

    # prompt = USER_PROMPT_TEMPLATE.format(
    #     input=question,
    #     context=context
    # )

    # response = llm.invoke(prompt)

    # Expected format:
    # ANSWER:
    # ...
    # SUMMARY:
    # ...
    return f"Question: {question}, Documents: {documents}, Audience: {audience}"

    
def run_query(args):
    """
    Execute a RAG query with audience-aware output.
    """
    # 1. Resolve configuration
    audience = args.audience
    top_k = args.top_k
    show_sources = args.show_sources
    question = args.question

    print(f"\n🔍 Querying CivicLens AI")
    print(f"Audience: {audience}")
    print(f"Top-K Retrieval: {top_k}")
    print("-" * 50)

    # 2. Retrieve relevant documents
    docs = retrieve_documents(
        query=question,
        top_k=top_k
    )

    if not docs:
        print("No relevant documents found.")
        return

    # 3. Generate grounded answer
    answer = generate_answer_and_summary(
        question=question,
        documents=docs,
        audience=audience
    )

    # 4. Display output
    print("\nANSWER:\n")
    print(answer)

    # print("\nSUMMARY:\n")
    # print(summary)

    # 5. Optional: show sources for transparency
    if show_sources:
        print("\nSOURCES:\n")
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "unknown")
            print(f"[{i}] {source}")


def run_info(args):
    """
    Display CivicLens AI system information.
    """
    info_data = {
        "name": "CivicLens AI",
        "description": (
            "A non-partisan AI system that translates complex U.S. government "
            "documents into clear, age-appropriate explanations."
        ),
        "audiences": [
            "Youth (ages 10-18)",
            "Policymakers and government leaders"
        ],
        "capabilities": [
            "Retrieval-Augmented Generation (RAG)",
            "Multi-audience explanations from a single source document",
            "Transparent source citation",
            "Document-grounded responses"
        ],
        "ethics_and_safeguards": [
            "No political persuasion or advocacy",
            "No partisan bias",
            "Explainable outputs",
            "Human-in-the-loop oversight"
        ],
        "deployment": [
            "Command-line interface (CLI)",
            "Chainlit interactive UI",
            "Local and S3-based document ingestion"
        ],
        "mission_alignment": [
            "AI education",
            "Civic literacy",
            "Responsible governance"
        ]
    }

    # -------------------------
    # JSON Output
    # -------------------------
    if args.json:
        import json
        print(json.dumps(info_data, indent=2))
        return

    # -------------------------
    # Short Text Output
    # -------------------------
    if args.short:
        print(
            "CivicLens AI is a non-partisan AI system that explains U.S. government "
            "documents in clear, age-appropriate language for youth and policymakers."
        )
        return

    # -------------------------
    # Full Text Output
    # -------------------------
    print("""
CivicLens AI
============

Purpose
-------
CivicLens AI is a non-partisan, responsible AI system designed to improve civic
literacy by translating complex U.S. government documents—such as Executive
Orders—into clear, accessible explanations.

Target Audiences
----------------
• Youth (ages 10–18)
• Policymakers and senior government leaders

Core Capabilities
-----------------
• Retrieval-Augmented Generation (RAG)
• Multi-audience explanations from a single source document
• Transparent source citation and traceability
• Faithfulness-focused evaluation

Ethics & Safeguards
------------------
• No political persuasion or advocacy
• No partisan bias
• Document-grounded responses only
• Explainable and auditable outputs
• Human oversight for high-impact decisions

Deployment
----------
• CLI (argparse-based)
• Chainlit interactive interface
• Local and S3 document ingestion

Mission Alignment
-----------------
CivicLens AI advances AI education, civic understanding, and responsible use of
artificial intelligence in governance.
""")

