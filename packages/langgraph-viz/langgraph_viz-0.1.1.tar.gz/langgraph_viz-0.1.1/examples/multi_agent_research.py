"""Example: Multi-Agent Research System with Supervisor.

This example demonstrates:
- Supervisor pattern coordinating multiple specialized agents
- Dynamic agent selection based on task requirements
- Collaborative workflow with agent specialization
- Complex branching and conditional routing
"""

from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver


# Define research state
class ResearchState(TypedDict):
    """State for multi-agent research system."""
    topic: str  # Research topic
    research_data: str  # Raw research findings
    summary: str  # Summarized information
    fact_check_result: str  # Fact-checking results
    final_report: str  # Final compiled report
    next_agent: str  # Which agent to invoke next
    iteration: int  # Current iteration count


def supervisor(state: ResearchState) -> ResearchState:
    """Supervisor agent that coordinates the research workflow."""
    print(f"\n🎯 SUPERVISOR: Analyzing task and delegating work...")
    
    iteration = state.get("iteration", 0)
    state["iteration"] = iteration + 1
    
    # Decide which agent to call next based on current state
    if not state.get("research_data"):
        # Need to gather research first
        state["next_agent"] = "researcher"
        print("   📋 Decision: Send to RESEARCHER to gather information")
    elif not state.get("summary"):
        # Have research, need summary
        state["next_agent"] = "summarizer"
        print("   📋 Decision: Send to SUMMARIZER to condense findings")
    elif not state.get("fact_check_result"):
        # Have summary, need fact-checking
        state["next_agent"] = "fact_checker"
        print("   📋 Decision: Send to FACT_CHECKER to verify accuracy")
    else:
        # All steps complete, generate final report
        state["next_agent"] = "finish"
        print("   📋 Decision: All agents complete, finishing up!")
    
    return state


def researcher(state: ResearchState) -> ResearchState:
    """Research agent that gathers information."""
    print(f"\n🔍 RESEARCHER: Gathering information on '{state['topic']}'...")
    
    topic = state["topic"]
    
    # Simulate research gathering (mock data)
    research_findings = f"""
    Research findings on {topic}:
    
    1. Primary Definition: {topic} is a key concept in modern technology.
    
    2. Key Statistics:
       - Used by 78% of industries worldwide
       - Market size estimated at $150B annually
       - Growing at 23% CAGR
    
    3. Main Applications:
       - Enterprise software solutions
       - Consumer applications
       - Scientific research tools
    
    4. Recent Developments:
       - New frameworks released in 2024
       - Integration with AI/ML systems
       - Enhanced security protocols
    
    5. Future Trends:
       - Expansion into emerging markets
       - Cloud-native architectures
       - Open-source community growth
    """
    
    state["research_data"] = research_findings.strip()
    print(f"   ✅ Gathered {len(research_findings)} characters of research data")
    print(f"   📊 Found 5 key points about {topic}")
    
    return state


def summarizer(state: ResearchState) -> ResearchState:
    """Summarization agent that condenses research findings."""
    print(f"\n📝 SUMMARIZER: Creating concise summary...")
    
    research_data = state.get("research_data", "")
    topic = state["topic"]
    
    # Simulate intelligent summarization
    summary = f"""
    EXECUTIVE SUMMARY: {topic}
    
    {topic} is a critical technology used across 78% of global industries, 
    with a market value of $150B growing at 23% annually. Key applications 
    span enterprise software, consumer apps, and scientific research.
    
    Recent 2024 developments include new frameworks, AI/ML integration, 
    and enhanced security. Future outlook shows expansion into emerging 
    markets, cloud-native adoption, and strong open-source growth.
    
    Recommendation: Strategic investment and early adoption recommended.
    """
    
    state["summary"] = summary.strip()
    print(f"   ✅ Created summary ({len(summary)} chars)")
    print(f"   📉 Reduced from {len(research_data)} to {len(summary)} chars")
    print(f"   💡 Compression ratio: {len(summary)/len(research_data)*100:.1f}%")
    
    return state


def fact_checker(state: ResearchState) -> ResearchState:
    """Fact-checking agent that verifies information accuracy."""
    print(f"\n✓ FACT_CHECKER: Verifying claims and statistics...")
    
    summary = state.get("summary", "")
    
    # Simulate fact-checking process
    print("   🔎 Checking statistical claims...")
    print("   🔎 Verifying market data...")
    print("   🔎 Validating growth projections...")
    
    fact_check = """
    FACT-CHECK REPORT:
    
    ✅ Market statistics verified against industry databases
    ✅ Growth rates confirmed by multiple sources
    ✅ Application domains validated
    ✅ Timeline of developments accurate
    
    Confidence Score: 94% - Information highly reliable
    
    Minor note: Some future projections are estimates based on current trends.
    Overall assessment: Report approved for publication.
    """
    
    state["fact_check_result"] = fact_check.strip()
    print(f"   ✅ Fact-check complete - 94% confidence score")
    print(f"   🎯 All major claims verified")
    
    return state


def compile_report(state: ResearchState) -> ResearchState:
    """Compile the final research report."""
    print(f"\n📄 COMPILER: Generating final report...")
    
    topic = state["topic"]
    summary = state.get("summary", "")
    fact_check = state.get("fact_check_result", "")
    
    final_report = f"""
    {'='*60}
    RESEARCH REPORT: {topic.upper()}
    {'='*60}
    
    {summary}
    
    ---
    
    VERIFICATION STATUS:
    {fact_check}
    
    ---
    
    Report compiled by Multi-Agent Research System
    All findings verified and approved for distribution.
    """
    
    state["final_report"] = final_report.strip()
    print(f"   ✅ Final report compiled!")
    print(f"   📈 Total length: {len(final_report)} characters")
    print(f"   🎉 Research process complete!")
    
    return state


def route_to_agent(state: ResearchState) -> str:
    """Route to the next agent based on supervisor decision."""
    next_agent = state.get("next_agent", "finish")
    print(f"\n➡️  Routing to: {next_agent.upper()}")
    return next_agent


def create_research_system():
    """Create the multi-agent research workflow."""
    workflow = StateGraph(ResearchState)
    
    # Add all agent nodes
    workflow.add_node("supervisor", supervisor)
    workflow.add_node("researcher", researcher)
    workflow.add_node("summarizer", summarizer)
    workflow.add_node("fact_checker", fact_checker)
    workflow.add_node("compiler", compile_report)
    
    # Start with supervisor
    workflow.set_entry_point("supervisor")
    
    # Supervisor routes to different agents
    workflow.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "researcher": "researcher",
            "summarizer": "summarizer",
            "fact_checker": "fact_checker",
            "finish": "compiler",
        }
    )
    
    # Each agent returns to supervisor for next decision
    workflow.add_edge("researcher", "supervisor")
    workflow.add_edge("summarizer", "supervisor")
    workflow.add_edge("fact_checker", "supervisor")
    
    # Compiler is the final step
    workflow.add_edge("compiler", END)
    
    # Compile with checkpointer
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


if __name__ == "__main__":
    print("=" * 70)
    print("🤝 LangGraph Viz - Multi-Agent Research System")
    print("=" * 70)
    
    from langgraph_viz import visualize
    
    # Create research system
    app = create_research_system()
    
    print("\n🎨 Starting visualization server...")
    print("📊 Watch how the supervisor coordinates multiple agents!")
    print("💡 Notice the dynamic routing between specialized agents\n")
    
    # Start visualization
    with visualize(app, port=8766) as viz_app:
        # Research topics to analyze
        topics = [
            "LangGraph Framework",
            "Multi-Agent AI Systems",
        ]
        
        for idx, topic in enumerate(topics, 1):
            print(f"\n{'='*70}")
            print(f"Research Task {idx}: {topic}")
            print('='*70)
            
            config = {"configurable": {"thread_id": f"research-{idx}"}}
            
            # Start research process
            input_state = {"topic": topic}
            
            # Stream execution
            print("\n🚀 Starting multi-agent research process...\n")
            for event in viz_app.stream(input_state, config):
                node_name = list(event.keys())[0]
                print(f"   ⚡ Executed: {node_name}")
            
            # Show final report
            final_state = viz_app.get_state(config)
            if final_state and final_state.values.get("final_report"):
                print(f"\n{final_state.values['final_report']}")
            
            print(f"\n{'='*70}")
            print(f"✅ Research on '{topic}' complete!")
            print(f"📊 Check visualization to see agent collaboration")
            print('='*70)
            
            # Pause between topics
            if idx < len(topics):
                import time
                time.sleep(3)
        
        print(f"\n{'='*70}")
        print("🎯 All research tasks complete!")
        print("💡 Notice how the supervisor coordinated 4 specialized agents")
        print("📈 Each agent contributed their expertise to the final report")
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
