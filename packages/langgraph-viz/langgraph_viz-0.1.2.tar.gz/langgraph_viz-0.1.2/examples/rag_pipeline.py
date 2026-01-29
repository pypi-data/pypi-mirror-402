"""Example: RAG Pipeline with Self-Correcting Retrieval.

This example demonstrates:
- Query analysis and rewriting
- Document retrieval from knowledge base
- Relevance checking and quality assessment
- Self-correcting loop with re-retrieval
- Context-aware response generation
"""

from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver


# Define RAG state
class RAGState(TypedDict):
    """State for RAG pipeline."""
    original_query: str  # User's original question
    analyzed_query: str  # Analyzed/rewritten query
    retrieved_docs: List[Dict[str, str]]  # Retrieved documents
    relevance_score: float  # Relevance assessment score
    retrieval_attempts: int  # Number of retrieval attempts
    final_answer: str  # Generated answer
    needs_reretrieval: bool  # Whether to retry retrieval


# Mock document database
KNOWLEDGE_BASE = {
    "langgraph": [
        {
            "id": "lg-001",
            "title": "LangGraph Introduction",
            "content": "LangGraph is a framework for building stateful, multi-actor applications with LLMs. It allows you to define workflows as graphs where nodes are functions and edges define the flow."
        },
        {
            "id": "lg-002",
            "title": "LangGraph State Management",
            "content": "LangGraph uses TypedDict to define state schemas. State is passed between nodes and can be checkpointed for persistence and time-travel debugging."
        },
        {
            "id": "lg-003",
            "title": "LangGraph Visualization",
            "content": "LangGraph can be visualized using tools like langgraph-viz which provide real-time insights into workflow execution, state changes, and node transitions."
        },
    ],
    "python": [
        {
            "id": "py-001",
            "title": "Python Basics",
            "content": "Python is a high-level, interpreted programming language known for its simplicity and readability. It supports multiple programming paradigms."
        },
        {
            "id": "py-002",
            "title": "Python Type Hints",
            "content": "Type hints in Python allow developers to specify expected types for function parameters and return values, improving code clarity and enabling static type checking."
        },
    ],
    "ai": [
        {
            "id": "ai-001",
            "title": "RAG Systems",
            "content": "Retrieval-Augmented Generation (RAG) combines retrieval systems with language models to provide grounded, factual responses based on a knowledge base."
        },
        {
            "id": "ai-002",
            "title": "Multi-Agent Systems",
            "content": "Multi-agent systems consist of multiple autonomous agents that collaborate to solve complex problems. Each agent has specialized capabilities."
        },
    ]
}


def analyze_query(state: RAGState) -> RAGState:
    """Analyze the user query and potentially rewrite it for better retrieval."""
    print(f"\n🔍 QUERY ANALYZER: Analyzing user query...")
    
    query = state["original_query"]
    print(f"   Original: '{query}'")
    
    # Simple query analysis - detect key topics
    query_lower = query.lower()
    
    if "visualize" in query_lower or "visualization" in query_lower:
        analyzed = query + " visualization tools"
    elif "state" in query_lower and "manage" in query_lower:
        analyzed = "state management system"
    elif "how" in query_lower:
        analyzed = query.replace("how does", "").replace("how do", "").strip()
    else:
        analyzed = query
    
    state["analyzed_query"] = analyzed
    print(f"   Analyzed: '{analyzed}'")
    print(f"   ✅ Query analysis complete")
    
    return state


def retrieve_documents(state: RAGState) -> RAGState:
    """Retrieve relevant documents from knowledge base."""
    print(f"\n📚 RETRIEVER: Searching knowledge base...")
    
    query = state["analyzed_query"]
    attempts = state.get("retrieval_attempts", 0) + 1
    state["retrieval_attempts"] = attempts
    
    print(f"   Retrieval attempt: {attempts}")
    print(f"   Query: '{query}'")
    
    # Simple keyword-based retrieval
    retrieved = []
    query_lower = query.lower()
    
    # Determine which domain to search
    if any(word in query_lower for word in ["langgraph", "graph", "workflow", "state", "visualize"]):
        docs = KNOWLEDGE_BASE["langgraph"]
        print(f"   🎯 Searching LangGraph domain...")
    elif any(word in query_lower for word in ["python", "type", "programming"]):
        docs = KNOWLEDGE_BASE["python"]
        print(f"   🎯 Searching Python domain...")
    elif any(word in query_lower for word in ["rag", "agent", "ai", "llm"]):
        docs = KNOWLEDGE_BASE["ai"]
        print(f"   🎯 Searching AI domain...")
    else:
        # Default: search all
        docs = KNOWLEDGE_BASE["langgraph"] + KNOWLEDGE_BASE["python"] + KNOWLEDGE_BASE["ai"]
        print(f"   🎯 Searching all domains...")
    
    # Retrieve top documents
    for doc in docs[:3]:  # Limit to top 3
        retrieved.append(doc)
    
    state["retrieved_docs"] = retrieved
    print(f"   ✅ Retrieved {len(retrieved)} documents")
    for doc in retrieved:
        print(f"      - {doc['title']} ({doc['id']})")
    
    return state


def check_relevance(state: RAGState) -> RAGState:
    """Assess the relevance of retrieved documents."""
    print(f"\n⚖️  RELEVANCE CHECKER: Assessing document quality...")
    
    query = state["analyzed_query"]
    docs = state.get("retrieved_docs", [])
    
    if not docs:
        score = 0.0
        print(f"   ❌ No documents retrieved - score: {score}")
    else:
        # Simple relevance scoring based on keyword overlap
        query_words = set(query.lower().split())
        
        total_score = 0
        for doc in docs:
            doc_words = set(doc["content"].lower().split())
            overlap = len(query_words & doc_words)
            doc_score = min(overlap / max(len(query_words), 1), 1.0)
            total_score += doc_score
        
        score = total_score / len(docs)
        score = round(score, 2)
        
        print(f"   📊 Analyzed {len(docs)} documents")
        print(f"   📈 Average relevance score: {score}")
    
    state["relevance_score"] = score
    
    # Decide if we need re-retrieval
    attempts = state.get("retrieval_attempts", 0)
    threshold = 0.3
    
    if score < threshold and attempts < 2:
        state["needs_reretrieval"] = True
        print(f"   ⚠️  Score below threshold ({threshold}) - will re-retrieve")
    else:
        state["needs_reretrieval"] = False
        if score >= threshold:
            print(f"   ✅ Score above threshold ({threshold}) - proceeding to generation")
        else:
            print(f"   ⚠️  Max attempts reached - proceeding with current docs")
    
    return state


def generate_answer(state: RAGState) -> RAGState:
    """Generate final answer using retrieved documents."""
    print(f"\n🤖 GENERATOR: Creating response...")
    
    query = state["original_query"]
    docs = state.get("retrieved_docs", [])
    relevance = state.get("relevance_score", 0)
    
    if not docs:
        answer = "I apologize, but I couldn't find relevant information to answer your question. Please try rephrasing your query."
    else:
        # Construct answer from documents
        context = "\n\n".join([f"- {doc['title']}: {doc['content']}" for doc in docs])
        
        answer = f"""Based on the knowledge base (relevance: {relevance:.0%}):

{context}

To answer your question: "{query}"

{docs[0]['content']} This information comes from {len(docs)} source(s) in our knowledge base."""
    
    state["final_answer"] = answer
    print(f"   ✅ Generated answer ({len(answer)} chars)")
    print(f"   📚 Used {len(docs)} document(s)")
    print(f"   🎯 Confidence: {relevance:.0%}")
    
    return state


def should_reretrieve(state: RAGState) -> str:
    """Decide whether to re-retrieve or proceed to generation."""
    if state. get("needs_reretrieval", False):
        print(f"\n🔄 ROUTING: Re-retrieving documents for better results")
        return "retrieve"
    else:
        print(f"\n✅ ROUTING: Proceeding to answer generation")
        return "generate"


def create_rag_pipeline():
    """Create the RAG workflow with self-correction."""
    workflow = StateGraph(RAGState)
    
    # Add nodes
    workflow.add_node("analyze_query", analyze_query)
    workflow.add_node("retrieve_documents", retrieve_documents)
    workflow.add_node("check_relevance", check_relevance)
    workflow.add_node("generate_answer", generate_answer)
    
    # Define flow
    workflow.set_entry_point("analyze_query")
    workflow.add_edge("analyze_query", "retrieve_documents")
    workflow.add_edge("retrieve_documents", "check_relevance")
    
    # Conditional edge: re-retrieve or generate
    workflow.add_conditional_edges(
        "check_relevance",
        should_reretrieve,
        {
            "retrieve": "retrieve_documents",  # Loop back for re-retrieval
            "generate": "generate_answer",     # Proceed to generation
        }
    )
    
    workflow.add_edge("generate_answer", END)
    
    # Compile with checkpointer
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


if __name__ == "__main__":
    print("=" * 70)
    print("📖 LangGraph Viz - RAG Pipeline with Self-Correction")
    print("=" * 70)
    
    from langgraph_viz import visualize
    
    # Create RAG pipeline
    app = create_rag_pipeline()
    
    print("\n🎨 Starting visualization server...")
    print("📊 Watch the self-correcting retrieval loop in action!")
    print("💡 Notice how the pipeline re-retrieves when relevance is low\n")
    
    # Start visualization
    with visualize(app, port=8765) as viz_app:
        # Test queries
        queries = [
            "What is LangGraph?",
            "How does LangGraph help with visualization?",
            "Tell me about Python type hints",
        ]
        
        for idx, query in enumerate(queries, 1):
            print(f"\n{'='*70}")
            print(f"Query {idx}: {query}")
            print('='*70)
            
            config = {"configurable": {"thread_id": f"rag-{idx}"}}
            
            # Run RAG pipeline
            input_state = {"original_query": query}
            
            print("\n🚀 Starting RAG pipeline...\n")
            for event in viz_app.stream(input_state, config):
                node_name = list(event.keys())[0]
                print(f"   ⚡ Executed: {node_name}")
            
            # Display final answer
            final_state = viz_app.get_state(config)
            if final_state and final_state.values.get("final_answer"):
                print(f"\n{'─'*70}")
                print("📄 FINAL ANSWER:")
                print('─'*70)
                print(final_state.values["final_answer"])
                print('─'*70)
            
            print(f"\n✅ Query {idx} complete - check visualization!")
            
            # Pause between queries
            if idx < len(queries):
                import time
                time.sleep(2)
        
        print(f"\n{'='*70}")
        print("🎯 All RAG queries complete!")
        print("💡 Notice the self-correcting behavior:")
        print("   - Query analysis rewrites unclear questions")
        print("   - Relevance checking evaluates document quality")
        print("   - Re-retrieval loop improves results")
        print('='*70)
        
        # Keep server running
        print("\n⏸️  Server running - Press Ctrl+C to exit\n")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down...")
    
    print("\n✓ Visualization complete!\n")
