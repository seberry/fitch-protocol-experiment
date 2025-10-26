# src/quiz_sampler.py
"""
Interactive Fitch Proof Quiz System with cumulative rule progression
"""
import random
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


from src.symbol_standardizer import standardize_symbols


class FitchQuizSampler:
    def __init__(self, problem_bank_file: str):
        self.problems = self.load_problems(problem_bank_file)
        self.current_quiz = []
    
    def load_problems(self, bank_file: str):
        problems = []
        with open(bank_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    problems.append(json.loads(line))
        return problems
    
    def filter_by_rules(self, allowed_rules: list):
        """Filter problems that only use specified rules"""
        if allowed_rules is None:
            return self.problems
            
        filtered = []
        for problem in self.problems:
            rules_used = problem['metadata']['rules_used']
            # Only include problems that use ONLY the allowed rules
            if all(rule in allowed_rules for rule in rules_used):
                filtered.append(problem)
        return filtered
    
    def create_quiz(self, num_questions: int = 5, allowed_rules: list = None):
        """Create a quiz with specified parameters"""
        pool = self.filter_by_rules(allowed_rules)
        
        if len(pool) < num_questions:
            print(f"⚠️  Only {len(pool)} problems available with these rules")
            num_questions = len(pool)
        
        self.current_quiz = random.sample(pool, min(num_questions, len(pool)))
        return self.current_quiz
    
       
    def display_question(self, question_num: int):
        """Display a single question with standardized symbols"""
        problem = self.current_quiz[question_num]
        
        # Standardize symbols for display
        standardized_premises = [standardize_symbols(p) for p in problem['premises']]
        standardized_conclusion = standardize_symbols(problem['conclusion'])
        standardized_solution = standardize_symbols(problem['ascii_solution'])
        
        print(f"\n{'='*60}")
        print(f"QUESTION {question_num + 1}")
        print(f"{'='*60}")
        print(f"Premises: {', '.join(standardized_premises)}")
        print(f"Conclusion: {standardized_conclusion}")
        print(f"\n This problem is doable using only the following rules: {', '.join(problem['metadata']['rules_used'])}")
        print(f"and this number of lines: {problem['metadata']['line_count']} lines")
        print(f"{'='*60}")
    
    def show_solution(self, question_num: int):
        """Show the solution with standardized symbols"""
        problem = self.current_quiz[question_num]
        standardized_solution = standardize_symbols(problem['ascii_solution'])
        
        print(f"\nSOLUTION for Question {question_num + 1}:")
        print(standardized_solution)
        print(f"\nRules used: {', '.join(problem['metadata']['rules_used'])}")

def interactive_quiz():
    """Interactive command-line quiz interface"""
    sampler = FitchQuizSampler("data/problems/fitch_problem_bank.jsonl")
    
    print("🎯 FITCH PROOF QUIZ SYSTEM")
    print("="*50)
    
    # Quiz configuration
    print("\n How many questions would you like?:")
    num_questions = int(input("Number of questions (1-10): ") or 5)

    # Updated rule sets in src/quiz_sampler.py
    print("\n📚 Available rule sets (cumulative progression):")
    print("1. Week 1: Basic rules (∧I, ∧E, →I, →E)")
    print("2. Week 2: + Disjunction & Biconditional (add ∨I, ∨E, ↔I, ↔E)")  
    print("3. Week 3: + Negation (add ¬I, ¬E, ⊥I, ⊥E)")
    print("4. All rules (including advanced rules)")

    choice = input("Choose rule set (1-4): ") or "4"

# Cumulative rule sets - each builds on the previous
    rule_sets = {
    "1": ["∧I", "∧E", "→I", "→E"],  # Basic rules only
    
    "2": ["∧I", "∧E", "→I", "→E",     # Basic + Disjunction + Biconditional
          "∨I", "∨E", "↔I", "↔E"],
          
    "3": ["∧I", "∧E", "→I", "→E",     # Basic + Disjunction + Biconditional + Negation
          "∨I", "∨E", "↔I", "↔E", 
          "¬I", "¬E", "⊥I", "⊥E"],
          
    "4": None  # All rules (no filtering)
    }

    
    # Create quiz
    quiz = sampler.create_quiz(
        num_questions=num_questions,
        allowed_rules=rule_sets.get(choice)
    )
    
    if not quiz:
        print("❌ No problems available with the selected rule set!")
        return
    
    print(f"\n✅ Quiz created with {len(quiz)} questions!")
    
    # Interactive session
    current_question = 0
    while current_question < len(quiz):
        sampler.display_question(current_question)
        
        action = input("\nOptions: [n]ext, [s]olution, [q]uit: ").lower()
        
        if action == 'n':
            current_question += 1
        elif action == 's':
            sampler.show_solution(current_question)
            input("\nPress Enter to continue...")
        elif action == 'q':
            break
    
    print("\n🎉 Quiz completed! Well done!")

if __name__ == "__main__":
    interactive_quiz()