"""
Simple workflow script for running the full experiment pipeline
"""
import sys
from pathlib import Path
from datetime import datetime
import io

# Fix Windows terminal encoding at the very top
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def find_latest_problems():
    """Find the most recent problems file"""
    problem_files = list(Path("data/problems").glob("problems_*.json"))
    if not problem_files:
        print("No problem files found. Please generate problems first.")
        return None
    latest = max(problem_files, key=lambda x: x.stat().st_mtime)
    return latest

def run_workflow():
    """Run the full workflow: generate problems → run experiment → harvest solutions"""
    print("🎯 FITCH PROOF EXPERIMENT WORKFLOW")
    print("="*50)
    
    # Step 1: Generate problems
    print("\n1. Generating problems...")
    from experiments.generate_and_save_problems import generate_problems_with_bundle
    bundle = input("Choose bundle (1=basic, 2=positive, 3=full) [2]: ") or "2"
    problems_file = generate_problems_with_bundle(bundle)
    
    if not problems_file:
        print("❌ Failed to generate problems")
        return
    
    # Step 2: Run experiment
    print(f"\n2. Running experiment on {problems_file}...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"data/results/experiment_{timestamp}"
    
    import subprocess
    result = subprocess.run([
        sys.executable, "experiments/run_experiment.py",
        "--problems", str(problems_file),
        "--output", output_dir + ".csv",
        "--model", "deepseek/deepseek-chat"
    ])
    
    if result.returncode != 0:
        print("❌ Experiment failed")
        return
    
    # Step 3: Harvest solutions
    print(f"\n3. Harvesting solutions from {output_dir}...")
    # We'll implement the harvest script next
    print("✅ Workflow complete!")
    
    # Step 4: Test quiz
    print(f"\n4. Testing quiz with expanded problem bank...")
    result = subprocess.run([
        sys.executable, "src/quiz_sampler.py"
    ])

if __name__ == "__main__":
    run_workflow()