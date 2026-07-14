import builtins
_print = builtins.print
def print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    _print(*args, **kwargs)

from orchestrator.graph import app

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        topic = sys.argv[1]
    else:
        try:
            topic = input("Enter the topic/question you want to orchestrate: ").strip()
            if not topic:
                print("Topic cannot be empty. Exiting.")
                exit(1)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            exit(0)

    inputs = {"topic": topic}
    
    print(f"\nRunning orchestrator-worker graph for: '{topic}'...")
    # Stream the execution so you can see each node running step-by-step
    for event in app.stream(inputs):
        for node, output in event.items():
            if node == "human_approval":
                continue
            print(f"\n================ Node: {node} ================")
            if node == "orchestrator":
                plan = output.get("plan")
                if plan:
                    print(f"Plan Created: {plan.overall_strategy}")
                    for task in plan.tasks:
                        print(f" - [{task.task_id}] ({task.worker_type}): {task.description} (Deps: {task.dependencies})")
            elif node == "worker":
                for res in output.get("results", []):
                    print(f"Task completed: {res['task_id']}")
                    print(f"\n--- Output of {res['task_id']} ({res['worker_type']}) ---")
                    print(res['output'])
                    print("-" * 50 + "\n")
            elif node == "synthesizer":
                print("\n=== FINAL REPORT ===")
                print(output["final_report"])
