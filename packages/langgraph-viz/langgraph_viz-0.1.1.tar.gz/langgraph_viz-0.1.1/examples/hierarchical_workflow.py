"""Example: Hierarchical Workflow with Subgraphs.

This example demonstrates:
- Workflow composition with subgraphs
- Parent graph invoking child graphs
- Modular workflow design
- Data pipeline pattern with nested workflows
- Hierarchical state management
"""

from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import random


# Define states for different levels
class DataPipelineState(TypedDict):
    """Main pipeline state."""
    input_data: List[Dict]  # Raw input data
    validation_result: str  # Input validation status
    processed_data: List[Dict]  # Processed data from subgraph
    analysis_results: Dict  # Analysis results from subgraph
    final_report: str  # Generated report
    pipeline_status: str  # Overall status


class ProcessingState(TypedDict):
    """Subgraph state for data processing."""
    raw_data: List[Dict]  # Input to processing
    cleaned_data: List[Dict]  # After cleaning
    transformed_data: List[Dict]  # After transformation
    quality_score: float  # Data quality metric


class AnalysisState(TypedDict):
    """Subgraph state for data analysis."""
    data: List[Dict]  # Input data
    statistics: Dict  # Statistical analysis
    insights: List[str]  # Generated insights
    confidence: float  # Analysis confidence


# ============================================================================
# DATA PROCESSING SUBGRAPH NODES
# ============================================================================

def clean_data(state: ProcessingState) -> ProcessingState:
    """Clean and normalize data."""
    print("      [Subgraph:Processing] 🧹 Cleaning data...")
    
    raw_data = state.get("raw_data", [])
    
    # Simulate data cleaning
    cleaned = []
    for item in raw_data:
        cleaned_item = {
            k: str(v).strip().lower() if isinstance(v, str) else v
            for k, v in item.items()
        }
        cleaned.append(cleaned_item)
    
    state["cleaned_data"] = cleaned
    print(f"      [Subgraph:Processing]    ✓ Cleaned {len(cleaned)} records")
    
    return state


def transform_data(state: ProcessingState) -> ProcessingState:
    """Transform data into target format."""
    print("      [Subgraph:Processing] 🔄 Transforming data...")
    
    cleaned = state.get("cleaned_data", [])
    
    # Simulate transformation
    transformed = []
    for item in cleaned:
        transformed_item = {
            **item,
            "processed": True,
            "quality_check": random.choice([True, True, True, False]),  # 75% pass
        }
        transformed.append(transformed_item)
    
    # Calculate quality score
    quality_checks = [item["quality_check"] for item in transformed]
    quality_score = sum(quality_checks) / len(quality_checks) if quality_checks else 0
    
    state["transformed_data"] = transformed
    state["quality_score"] = round(quality_score, 2)
    
    print(f"      [Subgraph:Processing]    ✓ Transformed {len(transformed)} records")
    print(f"      [Subgraph:Processing]    📊 Quality: {quality_score:.0%}")
    
    return state


def create_processing_subgraph():
    """Create the data processing subgraph."""
    subgraph = StateGraph(ProcessingState)
    
    subgraph.add_node("clean", clean_data)
    subgraph.add_node("transform", transform_data)
    
    subgraph.set_entry_point("clean")
    subgraph.add_edge("clean", "transform")
    subgraph.add_edge("transform", END)
    
    return subgraph.compile()


# ============================================================================
# DATA ANALYSIS SUBGRAPH NODES
# ============================================================================

def compute_statistics(state: AnalysisState) -> AnalysisState:
    """Compute statistical metrics."""
    print("      [Subgraph:Analysis] 📊 Computing statistics...")
    
    data = state.get("data", [])
    
    # Simulate statistical analysis
    stats = {
        "total_records": len(data),
        "valid_records": sum(1 for item in data if item.get("quality_check", False)),
        "average_quality": sum(item.get("quality_check", 0) for item in data) / len(data) if data else 0,
        "categories": len(set(item.get("category", "unknown") for item in data)),
    }
    
    state["statistics"] = stats
    print(f"      [Subgraph:Analysis]    ✓ Analyzed {stats['total_records']} records")
    print(f"      [Subgraph:Analysis]    📈 Quality: {stats['average_quality']:.0%}")
    
    return state


def generate_insights(state: AnalysisState) -> AnalysisState:
    """Generate insights from statistics."""
    print("      [Subgraph:Analysis] 💡 Generating insights...")
    
    stats = state.get("statistics", {})
    
    insights = []
    
    # Generate insights based on statistics
    if stats.get("valid_records", 0) == stats.get("total_records", 0):
        insights.append("✓ All records passed quality checks")
    elif stats.get("average_quality", 0) > 0.8:
        insights.append(f"✓ High quality dataset ({stats['average_quality']:.0%} valid)")
    else:
        insights.append(f"⚠ Data quality needs improvement ({stats['average_quality']:.0%} valid)")
    
    if stats.get("categories", 0) > 5:
        insights.append(f"📊 Rich dataset with {stats['categories']} categories")
    
    insights.append(f"📈 Processed {stats.get('total_records', 0)} total records")
    
    # Calculate confidence
    confidence = min(stats.get("average_quality", 0) + 0.2, 1.0)
    
    state["insights"] = insights
    state["confidence"] = round(confidence, 2)
    
    print(f"      [Subgraph:Analysis]    ✓ Generated {len(insights)} insights")
    print(f"      [Subgraph:Analysis]    🎯 Confidence: {confidence:.0%}")
    
    return state


def create_analysis_subgraph():
    """Create the data analysis subgraph."""
    subgraph = StateGraph(AnalysisState)
    
    subgraph.add_node("statistics", compute_statistics)
    subgraph.add_node("insights", generate_insights)
    
    subgraph.set_entry_point("statistics")
    subgraph.add_edge("statistics", "insights")
    subgraph.add_edge("insights", END)
    
    return subgraph.compile()


# ============================================================================
# MAIN PIPELINE NODES
# ============================================================================

def validate_input(state: DataPipelineState) -> DataPipelineState:
    """Validate input data."""
    print(f"\n✅ VALIDATOR: Checking input data...")
    
    input_data = state.get("input_data", [])
    
    if not input_data:
        state["validation_result"] = "❌ FAILED: No data provided"
        state["pipeline_status"] = "failed"
    elif len(input_data) < 1:
        state["validation_result"] = "❌ FAILED: Insufficient data"
        state["pipeline_status"] = "failed"
    else:
        state["validation_result"] = f"✓ PASSED: {len(input_data)} records valid"
        state["pipeline_status"] = "processing"
    
    print(f"   {state['validation_result']}")
    
    return state


def run_processing_pipeline(state: DataPipelineState) -> DataPipelineState:
    """Run the data processing subgraph."""
    print(f"\n🔄 PROCESSOR: Running data processing subgraph...")
    print(f"   Entering processing subgraph...")
    
    # Prepare input for subgraph
    processing_input = {
        "raw_data": state.get("input_data", [])
    }
    
    # Invoke processing subgraph
    processing_graph = create_processing_subgraph()
    result = processing_graph.invoke(processing_input)
    
    # Extract results
    state["processed_data"] = result.get("transformed_data", [])
    
    print(f"   ✓ Processing subgraph complete")
    print(f"   📦 Output: {len(state['processed_data'])} processed records")
    
    return state


def run_analysis_pipeline(state: DataPipelineState) -> DataPipelineState:
    """Run the data analysis subgraph."""
    print(f"\n📊 ANALYZER: Running analysis subgraph...")
    print(f"   Entering analysis subgraph...")
    
    # Prepare input for subgraph
    analysis_input = {
        "data": state.get("processed_data", [])
    }
    
    # Invoke analysis subgraph
    analysis_graph = create_analysis_subgraph()
    result = analysis_graph.invoke(analysis_input)
    
    # Extract results
    state["analysis_results"] = {
        "statistics": result.get("statistics", {}),
        "insights": result.get("insights", []),
        "confidence": result.get("confidence", 0)
    }
    
    print(f"   ✓ Analysis subgraph complete")
    print(f"   💡 Insights: {len(state['analysis_results']['insights'])}")
    
    return state


def generate_report(state: DataPipelineState) -> DataPipelineState:
    """Generate final report from all pipeline results."""
    print(f"\n📄 REPORTER: Generating final report...")
    
    analysis = state.get("analysis_results", {})
    stats = analysis.get("statistics", {})
    insights = analysis.get("insights", [])
    confidence = analysis.get("confidence", 0)
    
    report = f"""
{'='*70}
DATA PIPELINE REPORT
{'='*70}

PIPELINE STATUS: ✅ SUCCESS

INPUT VALIDATION:
{state.get('validation_result', 'N/A')}

PROCESSING RESULTS:
- Total Records Processed: {stats.get('total_records', 0)}
- Valid Records: {stats.get('valid_records', 0)}
- Data Quality: {stats.get('average_quality', 0):.0%}
- Categories Detected: {stats.get('categories', 0)}

KEY INSIGHTS:
"""
    
    for insight in insights:
        report += f"  {insight}\n"
    
    report += f"""
CONFIDENCE SCORE: {confidence:.0%}

PIPELINE SUMMARY:
✓ Input validation passed
✓ Data processing completed
✓ Statistical analysis completed
✓ Insights generated
✓ Report ready for distribution
{'='*70}
"""
    
    state["final_report"] = report.strip()
    state["pipeline_status"] = "completed"
    
    print(f"   ✅ Report generated")
    print(f"   📊 Confidence: {confidence:.0%}")
    
    return state


def create_hierarchical_pipeline():
    """Create the main pipeline with embedded subgraphs."""
    workflow = StateGraph(DataPipelineState)
    
    # Add main pipeline nodes
    workflow.add_node("validate", validate_input)
    workflow.add_node("process", run_processing_pipeline)  # Invokes processing subgraph
    workflow.add_node("analyze", run_analysis_pipeline)    # Invokes analysis subgraph
    workflow.add_node("report", generate_report)
    
    # Define main pipeline flow
    workflow.set_entry_point("validate")
    workflow.add_edge("validate", "process")
    workflow.add_edge("process", "analyze")
    workflow.add_edge("analyze", "report")
    workflow.add_edge("report", END)
    
    # Compile with checkpointer
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


if __name__ == "__main__":
    print("=" * 70)
    print("🏗️  LangGraph Viz - Hierarchical Workflow with Subgraphs")
    print("=" * 70)
    
    from langgraph_viz import visualize
    
    # Create hierarchical pipeline
    app = create_hierarchical_pipeline()
    
    print("\n🎨 Starting visualization server...")
    print("📊 Watch the hierarchical pipeline with nested subgraphs!")
    print("💡 Notice how subgraphs are invoked from the main workflow\n")
    
    # Start visualization
    with visualize(app, port=8765) as viz_app:
        # Sample datasets
        datasets = [
            {
                "name": "User Activity Dataset",
                "data": [
                    {"id": 1, "category": "web", "value": 100, "user": "Alice"},
                    {"id": 2, "category": "mobile", "value": 250, "user": "Bob"},
                    {"id": 3, "category": "web", "value": 180, "user": "Charlie"},
                    {"id": 4, "category": "api", "value": 320, "user": "Diana"},
                    {"id": 5, "category": "mobile", "value": 90, "user": "Eve"},
                ]
            },
            {
                "name": "Sales Transactions",
                "data": [
                    {"id": 1, "category": "electronics", "amount": 599, "region": "north"},
                    {"id": 2, "category": "books", "amount": 29, "region": "south"},
                    {"id": 3, "category": "electronics", "amount": 1299, "region": "east"},
                    {"id": 4, "category": "clothing", "amount": 89, "region": "west"},
                ]
            },
        ]
        
        for idx, dataset in enumerate(datasets, 1):
            print(f"\n{'='*70}")
            print(f"Pipeline Run {idx}: {dataset['name']}")
            print('='*70)
            
            config = {"configurable": {"thread_id": f"pipeline-{idx}"}}
            
            # Run pipeline
            input_state = {"input_data": dataset["data"]}
            
            print(f"\n🚀 Starting hierarchical pipeline...\n")
            for event in viz_app.stream(input_state, config):
                node_name = list(event.keys())[0]
                print(f"   ⚡ Main Pipeline: [{node_name}] completed")
            
            # Display final report
            final_state = viz_app.get_state(config)
            if final_state and final_state.values.get("final_report"):
                print(f"\n{final_state.values['final_report']}")
            
            print(f"\n{'='*70}")
            print(f"✅ Pipeline {idx} complete!")
            print('='*70)
            
            # Pause between runs
            if idx < len(datasets):
                import time
                time.sleep(2)
        
        print(f"\n{'='*70}")
        print("🎯 All pipeline runs complete!")
        print("💡 Hierarchical workflow patterns demonstrated:")
        print("   - Main pipeline coordinates high-level workflow")
        print("   - Processing subgraph handles data transformation")
        print("   - Analysis subgraph computes insights")
        print("   - Modular design enables reusability")
        print("   - State flows between parent and child graphs")
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
