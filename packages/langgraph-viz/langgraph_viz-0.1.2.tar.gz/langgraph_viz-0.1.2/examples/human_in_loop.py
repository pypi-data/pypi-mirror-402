"""Example: Human-in-the-Loop Approval Workflow.

This example demonstrates:
- Using interrupts to pause workflow execution
- Human approval/feedback integration
- State editing before continuation
- Multiple approval checkpoints
- Simulated approval with auto-continue
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import time


# Define workflow state
class DeploymentState(TypedDict):
    """State for deployment approval workflow."""
    service_name: str  # Service being deployed
    environment: str  # Target environment
    plan: str  # Deployment plan
    approval_status: str  # Current approval status
    tests_passed: bool  # Test results
    deployed: bool  # Deployment completed
    approvals_required: int  # How many approvals needed
    approvals_received: int  # How many approvals received
    feedback: List[str]  # Approval feedback/comments


def create_deployment_plan(state: DeploymentState) -> DeploymentState:
    """Create a deployment plan for the service."""
    print(f"\n📋 PLANNER: Creating deployment plan...")
    
    service = state["service_name"]
    env = state["environment"]
    
    plan = f"""
DEPLOYMENT PLAN
===============
Service: {service}
Environment: {env.upper()}
Time: {time.strftime('%Y-%m-%d %H:%M:%S')}

Steps:
1. Run pre-deployment tests
2. Create database backup
3. Stop current service instances
4. Deploy new version (v2.1.0)
5. Run smoke tests
6. Monitor for 5 minutes
7. Complete deployment

Risk Level: {'HIGH' if env == 'production' else 'MEDIUM'}
Rollback Plan: Automated rollback on failure
Expected Duration: 15 minutes
"""
    
    state["plan"] = plan.strip()
    state["approval_status"] = "pending"
    state["approvals_received"] = 0
    state["feedback"] = []
    
    print(f"   ✅ Deployment plan created for {service}")
    print(f"   🎯 Target: {env.upper()}")
    print(f"   ⏱️  Estimated duration: 15 minutes")
    
    return state


def request_approval(state: DeploymentState) -> DeploymentState:
    """Request human approval before proceeding."""
    print(f"\n⏸️  APPROVAL CHECKPOINT: Waiting for human review...")
    
    service = state["service_name"]
    env = state["environment"]
    approvals_received = state.get("approvals_received", 0)
    
    print(f"\n{'='*70}")
    print("📄 DEPLOYMENT PLAN READY FOR REVIEW")
    print('='*70)
    print(state["plan"])
    print('='*70)
    print(f"\n   👤 Approval {approvals_received + 1} of {state['approvals_required']} required")
    print(f"   ⚠️  This would normally INTERRUPT here for human input")
    print(f"   🤖 Auto-approving after 2 seconds for demo...\n")
    
    # Simulate human approval delay
    time.sleep(2)
    
    # Simulate approval
    state["approvals_received"] = approvals_received + 1
    state["feedback"].append(f"Approval {state['approvals_received']}: Looks good, proceed!")
    
    if state["approvals_received"] >= state["approvals_required"]:
        state["approval_status"] = "approved"
        print(f"   ✅ APPROVED by reviewer {state['approvals_received']}")
    else:
        state["approval_status"] = "partial"
        print(f"   ⏳ Partial approval ({state['approvals_received']}/{state['approvals_required']})")
    
    return state


def run_tests(state: DeploymentState) -> DeploymentState:
    """Run pre-deployment tests."""
    print(f"\n🧪 TEST RUNNER: Executing test suite...")
    
    print(f"   Running unit tests...")
    time.sleep(0.5)
    print(f"   ✓ Unit tests: 247 passed")
    
    print(f"   Running integration tests...")
    time.sleep(0.5)
    print(f"   ✓ Integration tests: 89 passed")
    
    print(f"   Running security scans...")
    time.sleep(0.5)
    print(f"   ✓ Security: No vulnerabilities")
    
    state["tests_passed"] = True
    print(f"\n   ✅ All tests passed!")
    
    return state


def request_deployment_approval(state: DeploymentState) -> DeploymentState:
    """Request final approval after tests."""
    print(f"\n⏸️  FINAL APPROVAL: Tests passed, ready to deploy...")
    
    print(f"\n{'='*70}")
    print("✅ TEST RESULTS - ALL PASSED")
    print('='*70)
    print("   ✓ Unit Tests: 247/247")
    print("   ✓ Integration Tests: 89/89")
    print("   ✓ Security Scans: Clean")
    print('='*70)
    print(f"\n   👤 Final approval required before deployment")
    print(f"   ⚠️  This would normally INTERRUPT here for human confirmation")
    print(f"   🤖 Auto-approving after 2 seconds for demo...\n")
    
    # Simulate approval delay
    time.sleep(2)
    
    # Record final approval
    approvals_received = state.get("approvals_received", 0)
    state["approvals_received"] = approvals_received + 1
    state["feedback"].append(f"Final approval: Tests look great, deploy!")
    state["approval_status"] = "approved"
    
    print(f"   ✅ APPROVED - Proceeding to deployment")
    
    return state


def execute_deployment(state: DeploymentState) -> DeploymentState:
    """Execute the actual deployment."""
    print(f"\n🚀 DEPLOYER: Executing deployment...")
    
    service = state["service_name"]
    env = state["environment"]
    
    steps = [
        "Creating database backup",
        "Stopping current instances",
        "Deploying new version",
        "Starting new instances",
        "Running smoke tests",
        "Monitoring health",
    ]
    
    for idx, step in enumerate(steps, 1):
        print(f"   [{idx}/{len(steps)}] {step}...")
        time.sleep(0.3)
        print(f"       ✓ Complete")
    
    state["deployed"] = True
    print(f"\n   ✅ Deployment successful!")
    print(f"   🎉 {service} is now live on {env.upper()}")
    
    return state


def verify_deployment(state: DeploymentState) -> DeploymentState:
    """Verify the deployment was successful."""
    print(f"\n🔍 VERIFIER: Checking deployment health...")
    
    checks = [
        ("Service health", "✓ Healthy"),
        ("Response time", "✓ 45ms avg"),
        ("Error rate", "✓ 0.01%"),
        ("Database connections", "✓ Optimal"),
    ]
    
    for check, result in checks:
        print(f"   {check}: {result}")
        time.sleep(0.2)
    
    print(f"\n   ✅ All health checks passed!")
    print(f"   📊 Deployment successful and verified")
    
    return state


def needs_more_approvals(state: DeploymentState) -> str:
    """Check if more approvals are needed."""
    approvals_received = state.get("approvals_received", 0)
    approvals_required = state.get("approvals_required", 1)
    
    if approvals_received < approvals_required:
        print(f"\n🔄 ROUTING: Need more approvals ({approvals_received}/{approvals_required})")
        return "request_more"
    else:
        print(f"\n✅ ROUTING: All approvals received, continuing...")
        return "proceed"


def create_approval_workflow():
    """Create the human-in-the-loop approval workflow."""
    workflow = StateGraph(DeploymentState)
    
    # Add nodes
    workflow.add_node("create_plan", create_deployment_plan)
    workflow.add_node("request_approval", request_approval)
    workflow.add_node("run_tests", run_tests)
    workflow.add_node("final_approval", request_deployment_approval)
    workflow.add_node("execute_deployment", execute_deployment)
    workflow.add_node("verify", verify_deployment)
    
    # Define flow
    workflow.set_entry_point("create_plan")
    workflow.add_edge("create_plan", "request_approval")
    
    # Conditional: might need multiple approvals
    workflow.add_conditional_edges(
        "request_approval",
        needs_more_approvals,
        {
            "request_more": "request_approval",  # Loop for more approvals
            "proceed": "run_tests",              # Continue to tests
        }
    )
    
    workflow.add_edge("run_tests", "final_approval")
    workflow.add_edge("final_approval", "execute_deployment")
    workflow.add_edge("execute_deployment", "verify")
    workflow.add_edge("verify", END)
    
    # Compile with checkpointer
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


if __name__ == "__main__":
    print("=" * 70)
    print("👥 LangGraph Viz - Human-in-the-Loop Approval Workflow")
    print("=" * 70)
    
    from langgraph_viz import visualize
    
    # Create approval workflow
    app = create_approval_workflow()
    
    print("\n🎨 Starting visualization server...")
    print("📊 Watch the approval checkpoints in action!")
    print("💡 In production, these would pause for human input\n")
    
    # Start visualization
    with visualize(app, port=8765) as viz_app:
        # Deployment scenarios
        deployments = [
            {
                "service_name": "payment-service",
                "environment": "production",
                "approvals_required": 2,  # Production needs 2 approvals
            },
            {
                "service_name": "user-api",
                "environment": "staging",
                "approvals_required": 1,  # Staging needs 1 approval
            },
        ]
        
        for idx, deployment in enumerate(deployments, 1):
            print(f"\n{'='*70}")
            print(f"Deployment {idx}: {deployment['service_name']} → {deployment['environment'].upper()}")
            print('='*70)
            
            config = {"configurable": {"thread_id": f"deploy-{idx}"}}
            
            # Start deployment workflow
            print(f"\n🚀 Starting approval workflow...\n")
            for event in viz_app.stream(deployment, config):
                node_name = list(event.keys())[0]
                print(f"      [{node_name}] completed")
            
            # Show final state
            final_state = viz_app.get_state(config)
            if final_state and final_state.values:
                state = final_state.values
                print(f"\n{'='*70}")
                print("📊 DEPLOYMENT SUMMARY")
                print('='*70)
                print(f"   Service: {state.get('service_name')}")
                print(f"   Environment: {state.get('environment', '').upper()}")
                print(f"   Status: {'✅ DEPLOYED' if state.get('deployed') else '❌ FAILED'}")
                print(f"   Approvals: {state.get('approvals_received')}/{state.get('approvals_required')}")
                print(f"   Tests: {'✅ PASSED' if state.get('tests_passed') else '❌ FAILED'}")
                print(f"\n   Feedback:")
                for feedback in state.get('feedback', []):
                    print(f"      💬 {feedback}")
                print('='*70)
            
            # Pause between deployments
            if idx < len(deployments):
                time.sleep(2)
        
        print(f"\n{'='*70}")
        print("🎯 All deployments complete!")
        print("💡 Key patterns demonstrated:")
        print("   - Multiple approval checkpoints")
        print("   - Conditional approval loops")
        print("   - State preservation during pauses")
        print("   - Progressive workflow execution")
        print('='*70)
        
        # Keep server running
        print("\n⏸️  Server running - Press Ctrl+C to exit\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down...")
    
    print("\n✓ Visualization complete!\n")
