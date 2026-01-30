import argparse
import csv
import re
import os
import sys
import math
import collections
import itertools
from datetime import datetime
from tqdm import tqdm
from datasets import load_dataset
from llama_cpp import Llama, LlamaGrammar

# ==========================================
# 1. Configuration
# ==========================================
TASK_CONFIG = {
    "logic": {
        "dataset_name": "winogrande",
        "subset": "winogrande_xs",
        "split": "validation",
        "type": "multiple_choice",
        "options": ["1", "2"],
        "prompt_template": "Complete the sentence: {sentence}\nOptions:\n1. {option1}\n2. {option2}\nAnswer (1 or 2): "
    },
    "grammar": {
        "dataset_name": "glue",
        "subset": "cola",
        "split": "validation",
        "type": "multiple_choice",
        "options": ["0", "1"], 
        "prompt_template": "Is this sentence grammatically correct?\nSentence: \"{sentence}\"\nAnswer 1 for Yes, 0 for No.\nAnswer: "
    },
    "nlp": {
        "dataset_name": "hellaswag",
        "subset": None,
        "split": "validation",
        "type": "multiple_choice",
        "options": ["0", "1", "2", "3"],
        "prompt_template": "Context: {ctx}\nWhich ending makes the most sense?\n0. {end0}\n1. {end1}\n2. {end2}\n3. {end3}\nAnswer: "
    },
    # --- NEW DATASET 1: AI2 Reasoning Challenge (Science/Reasoning) ---
    "science": {
        "dataset_name": "ai2_arc",
        "subset": "ARC-Challenge",
        "split": "test",
        "type": "multiple_choice",
        "options": ["A", "B", "C", "D"], 
        "prompt_template": "Question: {question}\nOptions:\n{choices_formatted}\nAnswer ({option_keys}): "
    },
    # --- NEW DATASET 2: PIQA (Physical Interaction) ---
    "physical_logic": {
        "dataset_name": "piqa",
        "subset": None,
        "split": "validation",
        "type": "multiple_choice",
        "options": ["0", "1"],
        "prompt_template": "Goal: {goal}\nWhich solution is better?\n0. {sol1}\n1. {sol2}\nAnswer (0 or 1): "
    },
    # --- NEW DATASET 3: OpenBookQA (Common Sense) ---
    "common_sense": {
        "dataset_name": "openbookqa",
        "subset": "main",
        "split": "test",
        "type": "multiple_choice",
        "options": ["A", "B", "C", "D"],
        "prompt_template": "Question: {question}\nOptions:\n{choices_formatted}\nAnswer ({option_keys}): "
    },
    "math": {
        "dataset_name": "gsm8k",
        "subset": "main",
        "split": "test",
        "type": "generation",
        "prompt_template": (
            "Question: A bag has 5 red balls and 3 blue balls. How many balls are there in total?\n"
            "Answer: There are 5 red balls and 3 blue balls. Total = 5 + 3 = 8. The answer is [8].\n\n"
            "Question: {question}\n"
            "Answer:"
        )
    },
    "programming": {
        "dataset_name": "mbpp",
        "subset": "sanitized",
        "split": "test",
        "type": "generation",
        "prompt_template": "Write a Python function to solve this:\n{text_code}\n\n```python\n"
    }
}

# ==========================================
# 2. The Evaluator Engine
# ==========================================
class ModelEvaluator:
    def __init__(self, model_path, n_ctx=4096, n_threads=8, n_gpu_layers=-1):
        """
        Initialize the model evaluator with GPU support.
        
        Args:
            model_path: Path to the GGUF model file
            n_ctx: Context window size
            n_threads: Number of CPU threads
            n_gpu_layers: Number of layers to offload to GPU (-1 = all layers)
        """
        print(f"Loading model from: {model_path}...")
        print(f"GPU Layers: {n_gpu_layers} (-1 means all layers)")
        
        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=n_gpu_layers,  # -1 = offload ALL layers to GPU
            n_batch=512,                 # Batch size for prompt processing
            verbose=True                 # Shows CUDA usage info
        )
        print("\n✓ Model loaded successfully!")
        print("=" * 60)
    
    def evaluate(self, task_name, limit):
        config = TASK_CONFIG[task_name]
        print(f"\n[+] SWITCHING DATABASE TO: {config['dataset_name'].upper()} ({task_name})")
        
        try:
            ds = load_dataset(config['dataset_name'], config['subset'], split=config['split'], trust_remote_code=True)
            ds = ds.shuffle(seed=42).select(range(min(limit, len(ds))))
        except Exception as e:
            print(f"Error loading dataset: {e}")
            return [], 0

        results = []
        correct_count = 0

        grammar = None
        if config['type'] == 'multiple_choice':
            options_str = ' | '.join(f'"{opt}"' for opt in config['options'])
            grammar_str = f'root ::= ({options_str})'
            grammar = LlamaGrammar.from_string(grammar_str, verbose=False)

        for i, item in tqdm(enumerate(ds), total=len(ds), desc=f"Testing {task_name}"):
            
            prompt = self._format_prompt(task_name, item, config)
            expected = self._get_expected_answer(task_name, item)
            response = ""

            try:
                if config['type'] == 'multiple_choice':
                    output = self.llm(prompt, max_tokens=5, temperature=0.0, grammar=grammar)
                    response = output['choices'][0]['text'].strip()
                
                elif task_name == "math":
                    output = self.llm(
                        prompt, 
                        max_tokens=1024, 
                        temperature=0.6, 
                        repeat_penalty=1.2,
                        stop=["Question:", "\n\n\n"]
                    )
                    response = output['choices'][0]['text'].strip()
                
                elif task_name == "programming":
                    output = self.llm(prompt, max_tokens=1024, temperature=0.2, stop=["```", "\n\nUser"])
                    response = output['choices'][0]['text'].strip()

            except Exception as e:
                response = f"ERROR: {e}"

            is_correct = self._check_answer(task_name, response, expected, item)
            
            if is_correct:
                correct_count += 1
            elif i == 0: 
                print(f"\n[DEBUG FAILURE] ID: {i}")
                print(f"Expected: {expected}")
                print(f"Response: {response}\n")

            results.append({
                "id": i,
                "prompt_snippet": prompt.replace("\n", " ")[:50] + "...",
                "expected": str(expected)[:100],
                "response": response[:100],
                "correct": is_correct
            })

        accuracy = (correct_count / len(ds)) * 100
        print(f"\nFinished Task: {task_name}. Accuracy: {accuracy:.2f}%")
        return results, accuracy

    def _format_prompt(self, task, item, config):
        if task == "logic":
            return config['prompt_template'].format(sentence=item['sentence'], option1=item['option1'], option2=item['option2'])
        elif task == "grammar":
            return config['prompt_template'].format(sentence=item['sentence'])
        elif task == "nlp":
            return config['prompt_template'].format(ctx=item['ctx'], end0=item['endings'][0], end1=item['endings'][1], end2=item['endings'][2], end3=item['endings'][3])
        
        # --- NEW FORMATTERS ---
        elif task == "physical_logic": 
            return config['prompt_template'].format(goal=item['goal'], sol1=item['sol1'], sol2=item['sol2'])
        
        elif task in ["science", "common_sense"]: 
            choices_text = item['choices']['text']
            choices_label = item['choices']['label']
            formatted_options = "\n".join([f"{l}. {t}" for l, t in zip(choices_label, choices_text)])
            keys_str = "/".join(choices_label)
            return config['prompt_template'].format(question=item['question_stem'] if 'question_stem' in item else item['question'], choices_formatted=formatted_options, option_keys=keys_str)
        # ----------------------

        elif task == "math":
            return config['prompt_template'].format(question=item['question'])
        elif task == "programming":
            return config['prompt_template'].format(text_code=item['prompt'])
        return ""

    def _get_expected_answer(self, task, item):
        if task == "logic": return item['answer']
        if task == "grammar": return str(item['label'])
        if task == "nlp": return str(item['label'])
        
        # --- NEW EXPECTED ANSWERS ---
        if task == "physical_logic": return str(item['label']) 
        if task in ["science", "common_sense"]: return item['answerKey'] 
        # ----------------------------

        if task == "math": return item['answer'].split("####")[-1].strip()
        if task == "programming": return item['code']
        return ""

    def _check_answer(self, task, response, expected, item=None):
        if task == "programming":
            return self._check_programming(response, expected, item)

        if task == "math":
            clean_response = response.replace(",", "")
            clean_expected = expected.replace(",", "")
            
            bracket_match = re.search(r"\[([\d,.]+)\]", response)
            if bracket_match:
                extracted = bracket_match.group(1).replace(",", "")
                try: return float(extracted) == float(clean_expected)
                except: return extracted == clean_expected

            explicit_match = re.search(r"[Tt]he answer is:?\s*(\-?\d+\.?\d*)", clean_response)
            if explicit_match:
                extracted = explicit_match.group(1)
                try: return float(extracted) == float(clean_expected)
                except: pass

            nums = re.findall(r"[-+]?\d*\.\d+|\d+", clean_response)
            if not nums: return False
            extracted = nums[-1]
            try: return float(extracted) == float(clean_expected)
            except: return extracted == clean_expected
            
        return response.strip() == expected.strip()

    def _check_programming(self, response, expected_code, item):
        generated_code = response
        if "```" in generated_code:
            generated_code = generated_code.split("```")[0]
        
        exp_name_match = re.search(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)", expected_code)
        gen_name_match = re.search(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)", generated_code)

        if not exp_name_match or not gen_name_match: return False

        expected_func_name = exp_name_match.group(1)
        generated_func_name = gen_name_match.group(1)

        local_scope = {"math": math, "re": re, "collections": collections, "itertools": itertools}

        try:
            exec(generated_code, {}, local_scope)
            if expected_func_name != generated_func_name:
                if generated_func_name in local_scope:
                    local_scope[expected_func_name] = local_scope[generated_func_name]
                else:
                    return False

            test_cases = item.get('test_list', [])
            for test in test_cases:
                exec(test, {}, local_scope)
            return True
        except Exception:
            return False

# ==========================================
# 3. CLI Entry Point
# ==========================================
def main():
    parser = argparse.ArgumentParser(description="Multi-Task Model Validator with GPU Support")
    parser.add_argument("--model", type=str, required=True, help="Path to .gguf file")
    parser.add_argument("--task", type=str, required=True, 
                        choices=["logic", "grammar", "nlp", "science", "physical_logic", "common_sense", "math", "programming"], 
                        help="Which dataset to load")
    parser.add_argument("--limit", type=int, default=10, help="How many samples to validate")
    parser.add_argument("--gpu-layers", type=int, default=-1, 
                        help="Number of layers to offload to GPU (-1 = all, 0 = CPU only)")
    parser.add_argument("--ctx-size", type=int, default=4096, help="Context window size")
    
    args = parser.parse_args()

    print("=" * 60)
    print("MULTI-TASK MODEL EVALUATOR")
    print("=" * 60)
    print(f"Model: {args.model}")
    print(f"Task: {args.task}")
    print(f"Samples: {args.limit}")
    print(f"Context Size: {args.ctx_size}")
    print(f"GPU Layers: {args.gpu_layers}")
    print("=" * 60)

    evaluator = ModelEvaluator(args.model, n_ctx=args.ctx_size, n_gpu_layers=args.gpu_layers)
    results, accuracy = evaluator.evaluate(args.task, args.limit)

    filename = f"results_{args.task}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "prompt_snippet", "expected", "response", "correct"])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n✓ Results saved to: {filename}")
    print(f"✓ Final Accuracy: {accuracy:.2f}%")

if __name__ == "__main__":
    main()