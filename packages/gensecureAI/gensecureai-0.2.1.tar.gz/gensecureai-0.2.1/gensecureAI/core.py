import ast
import os
import inspect
import tkinter as tk
import subprocess
import shutil
import difflib
from tkinter import ttk, messagebox, simpledialog, filedialog
from groq import Groq
from rich.console import Console
from dotenv import load_dotenv

console = Console()

# --- Configuration & Persistence ---
CONFIG_FILE = "gensecure_config.txt"
DEFAULT_GROQ_API_KEY = "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"
MODEL_ID = "openai/gpt-oss-120b"

def load_api_key():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                saved_key = f.read().strip()
                return saved_key if saved_key else DEFAULT_GROQ_API_KEY
        except:
            return DEFAULT_GROQ_API_KEY
    return DEFAULT_GROQ_API_KEY

def save_api_key(api_key):
    try:
        with open(CONFIG_FILE, "w") as f:
            f.write(api_key.strip())
    except Exception as e:
        console.print(f"[bold red]Failed to save config: {e}[/bold red]")

class SecureGenAI:
    def __init__(self, file_path):
        self.file_path = file_path
        self.current_key = load_api_key()
        if not os.path.exists(file_path):
            return
        with open(file_path, "r", encoding="utf-8") as f:
            self.code = f.read()
        self.vulnerabilities = []
        self.risk_score = 100

    # --- 🔬 AST DIFF GUARD (Hard Constraint Mode) ---
    def get_structural_fingerprint(self, source_code):
        """Extracts function/class names and their signatures to ensure AI logic stays intact."""
        try:
            tree = ast.parse(source_code)
            names = set()
            for node in ast.walk(tree):
                # We track Classes and Functions (Async and Sync)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    names.add(node.name)
            return names
        except Exception:
            return set()

    # --- 📊 RESEARCH-GRADE METRICS EXPORT ---
    def export_research_metrics(self, fixed_status, trust_score):
        import json
        metrics_path = "security_metrics.json"
        
        # Calculate stats
        total_v = len(self.vulnerabilities)
        # Assuming fixed if status is True, false_positives can be flagged by user later 
        # but for auto-export we track basic counts
        data = {
            "file": os.path.basename(self.file_path),
            "vulnerabilities_detected": total_v,
            "fix_applied": fixed_status,
            "trust_score": trust_score,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }

        try:
            with open(metrics_path, "w") as f:
                json.dump(data, f, indent=2)
            console.print(f"[bold cyan]📊 Metrics exported to {metrics_path}[/bold cyan]")
        except Exception as e:
            console.print(f"[bold red]Metrics Export Failed: {e}[/bold red]")
    # --- 🧠 HUMAN TRUST SCORE METRIC ---
    def calculate_trust_score(self, original_code, fixed_code):
        trust = 100
        try:
            # 1. Check Line Changes (-20 if > 10 lines changed)
            orig_lines = original_code.splitlines()
            fixed_lines = fixed_code.splitlines()
            diff = list(difflib.ndiff(orig_lines, fixed_lines))
            changes = [l for l in diff if l.startswith('+ ') or l.startswith('- ')]
            if len(changes) > 10:
                trust -= 20

            # 2. Check New Imports (-30 if new external libraries added)
            def get_imports(code):
                tree = ast.parse(code)
                return {n.name for node in ast.walk(tree) if isinstance(node, ast.Import) for n in node.names} | \
                       {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}

            new_imports = get_imports(fixed_code) - get_imports(original_code)
            if new_imports:
                trust -= 30

            # 3. Logic Branch Change (-25 if if/while/for loops count changed)
            def count_branches(code):
                tree = ast.parse(code)
                return len([n for n in ast.walk(tree) if isinstance(n, (ast.If, ast.While, ast.For, ast.Try))])

            if count_branches(original_code) != count_branches(fixed_code):
                trust -= 25

            return max(0, trust)
        except:
            return 50 # Default to neutral if analysis fails
    def validate_ast_integrity(self, original_code, fixed_code):
        """Hard Constraint: Rejects AI fix if it changes the code structure."""
        orig_names = self.get_structural_fingerprint(original_code)
        
        try:
            fixed_names = self.get_structural_fingerprint(fixed_code)
        except SyntaxError:
            return False, "AST Guard Error: AI returned code with Syntax Errors."

        # 1. Detection of Deletion/Renaming (Crucial for Functional Equivalence)
        missing = orig_names - fixed_names
        if missing:
            return False, f"Structural Violation: AI removed or renamed functions/classes: {', '.join(missing)}"
        
        # 2. Detection of Unauthorized Bloat/Hallucinations
        added = fixed_names - orig_names
        if added:
            return False, f"Structural Violation: AI added unauthorized new structures: {', '.join(added)}"
        
        return True, "Structure Verified"

    def scan(self):
        if not self.code: return self
        try:
            tree = ast.parse(self.code)
            for node in ast.walk(tree):
                # SQL Injection Check
                if isinstance(node, (ast.BinOp, ast.JoinedStr)):
                    try:
                        code_snippet = ast.unparse(node).upper()
                        if any(k in code_snippet for k in ["SELECT", "INSERT", "UPDATE", "DELETE", "DROP"]):
                            self._add_v(node, "SQL Injection", "CRITICAL", "CWE-89")
                    except: continue
                
                # Command Injection Check
                if isinstance(node, ast.Call):
                    try:
                        func_name = ast.unparse(node.func)
                        if any(x in func_name for x in ["os.system", "os.popen", "subprocess.call"]):
                            self._add_v(node, "OS Command Injection", "CRITICAL", "CWE-78")
                        if func_name in ["eval", "exec", "compile"]:
                            self._add_v(node, "Code Injection", "CRITICAL", "CWE-94")
                    except: continue

                # Hardcoded Secrets
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            t_name = target.id.upper()
                            if any(s in t_name for s in ["API_KEY", "SECRET", "PASSWORD", "TOKEN", "PWD"]):
                                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                                    self._add_v(node, "Hardcoded Secret", "CRITICAL", "CWE-798")

            critical_count = len([v for v in self.vulnerabilities if v.get("risk") == "CRITICAL"])
            self.risk_score = max(0, 100 - (critical_count * 20) - (len(self.vulnerabilities) * 5))
            self.generate_html_report()
        except Exception as e:
            console.print(f"[bold red]Scan Error: {e}[/bold red]")
        return self

    def _add_v(self, node, name, risk, cwe):
        self.vulnerabilities.append({
            "line": getattr(node, 'lineno', 'N/A'),
            "name": name, "risk": risk, "cwe": cwe
        })

    def get_ai_fix(self):
        try:
            # 1️⃣ Identify specific vulnerability types
            found_cwes = list(set([v['cwe'] for v in self.vulnerabilities]))
        
            # 2️⃣ Inject CWE-specific repair rules
            repair_rules = ""
            if "CWE-89" in found_cwes:
                repair_rules += "- For CWE-89: ONLY modify SQL execution lines. Use parameterized queries. Do NOT touch surrounding logic.\n"
            if "CWE-78" in found_cwes:
                repair_rules += "- For CWE-78: ONLY modify OS command calls. Use subprocess.run(['cmd', 'arg'], shell=False).\n"
            if "CWE-94" in found_cwes:
                repair_rules += "- For CWE-94: ONLY replace eval/exec with safe alternatives like ast.literal_eval.\n"
            if "CWE-798" in found_cwes:
                repair_rules += "- For CWE-798: ONLY replace hardcoded strings with os.getenv().\n"

            # --- YAHAN SE BAHAR HONA CHAHIYE (Correct Indentation) ---
            client = Groq(api_key=self.current_key)
            prompt = f"""
[ROLE] 
Principal Application Security Engineer. Perform a surgical patch.

[OBJECTIVE]
Fix ONLY these detected vulnerabilities: {', '.join(found_cwes)}.

[STRICT REPAIR RULES - MULTI-STEP CONTEXT]
{repair_rules if repair_rules else "- Focus on general secure coding best practices."}
- DO NOT refactor, rename, or move any unrelated code blocks.
- DO NOT change the signature of any function or class.

[STRICT CONSTRAINTS - AST GUARD IS ACTIVE]
1. DO NOT change, rename, or remove any 'def' or 'class' statements.
2. DO NOT add new functions, classes, or imports.
3. Return ONLY the raw Python source code. 
4. NO markdown, NO code fences (```), NO explanations.

[INPUT CODE]
{self.code}

[OUTPUT]
Return ONLY the corrected Python code.
"""

            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            fixed_code = response.choices[0].message.content.strip()
            
            # Clean markdown
            if "```" in fixed_code:
                fixed_code = fixed_code.split("```python")[-1].split("```")[0].strip()

            # --- 🛡️ AST GUARD ENFORCEMENT ---
            is_valid, error_msg = self.validate_ast_integrity(self.code, fixed_code)
            if not is_valid:
                console.print(f"[bold red]AST GUARD REJECTED FIX: {error_msg}[/bold red]")
                messagebox.showerror("AST Guard Violation", 
                                   f"The AI attempted to change the structure of your code.\n\nReason: {error_msg}")
                return None
            
            return fixed_code

        except Exception as e:
            console.print(f"[bold red]AI Fix Error: {e}[/bold red]")
            return None

    def show_diff_window(self, old_code, new_code, output_file):
        trust_score = self.calculate_trust_score(old_code, new_code)
        diff_win = tk.Toplevel()
        diff_win.title("Vulnerability Comparison (AST-Guided Diff)| Trust Score: {trust_score}%")
        diff_win.geometry("900x650")
        diff_win.configure(bg="#0D0D0D")
        # Trust Score Header
        trust_color = "#00FF00" if trust_score > 70 else "#FFD700" if trust_score > 40 else "#FF3131"
        tk.Label(diff_win, text=f"CODE FIX TRUST SCORE: {trust_score}%", 
                 bg="#1A1A1A", fg=trust_color, font=("Arial", 12, "bold"), pady=10).pack(fill="x")

        tk.Label(diff_win, text="🔴 REMOVED/INSECURE | 🟢 ADDED/SECURED (Structure preserved by AST Guard)", 
                 bg="#0D0D0D", fg="white", font=("Arial", 9, "bold")).pack(pady=5)

        txt_frame = tk.Frame(diff_win, bg="#0D0D0D")
        txt_frame.pack(fill="both", expand=True, padx=10, pady=5)

        diff_text = tk.Text(txt_frame, bg="#111111", fg="white", font=("Consolas", 10))
        diff_text.pack(side="left", fill="both", expand=True)
        
        scroll = tk.Scrollbar(txt_frame, command=diff_text.yview)
        scroll.pack(side="right", fill="y")
        diff_text.config(yscrollcommand=scroll.set)

        diff = difflib.ndiff(old_code.splitlines(), new_code.splitlines())
        for line in diff:
            if line.startswith('- '):
                diff_text.insert("end", line + "\n", "removed")
            elif line.startswith('+ '):
                diff_text.insert("end", line + "\n", "added")
            elif not line.startswith('? '):
                diff_text.insert("end", line + "\n")

        diff_text.tag_config("removed", background="#4B0000", foreground="#FFCCCC")
        diff_text.tag_config("added", background="#003300", foreground="#CCFFCC")
        diff_text.config(state="disabled")

        def final_save():
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(new_code)
            # --- Trigger Research Export ---
            self.export_research_metrics(fixed_status=True, trust_score=trust_score)
            messagebox.showinfo("Success", f"Fixed code saved to {output_file}")
            diff_win.destroy()

        tk.Button(diff_win, text="CONFIRM & APPLY SECURE FIX", command=final_save, 
                  bg="#008037", fg="white", font=("Arial", 10, "bold"), padx=20).pack(pady=10)

    def generate_html_report(self):
        report_path = "security_report.html"
        html = f"<html><body style='font-family:sans-serif;background:#f4f4f4;'><h1>Security Audit: {os.path.basename(self.file_path)}</h1>"
        html += f"<h3>Risk Score: {self.risk_score}%</h3><table border='1'><tr><th>Line</th><th>Issue</th><th>Risk</th></tr>"
        for v in self.vulnerabilities:
            html += f"<tr><td>{v['line']}</td><td>{v['name']}</td><td>{v.get('risk','N/A')}</td></tr>"
        html += "</table></body></html>"
        with open(report_path, "w") as f: f.write(html)

    def open_settings(self):
        new_key = simpledialog.askstring("Settings", "Update Groq API Key:", initialvalue=self.current_key)
        if new_key:
            self.current_key = new_key
            save_api_key(new_key)

    def show_dependency_map(self):
        dep_win = tk.Toplevel()
        dep_win.title("📦 Dependency Security Map")
        dep_win.geometry("400x500")
        dep_win.configure(bg="#0D0D0D")
        tk.Label(dep_win, text="IMPORTED LIBRARIES ANALYSIS", bg="#0D0D0D", fg="#00FF00", font=("Arial", 10, "bold")).pack(pady=10)
        tree_frame = tk.Frame(dep_win, bg="#111111")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        dep_tree = ttk.Treeview(tree_frame, columns=("Status"), show="tree headings")
        dep_tree.heading("#0", text="Library")
        dep_tree.heading("Status", text="Status")
        danger_libs = ["pickle", "subprocess", "os", "marshal", "hashlib"]
        try:
            parsed = ast.parse(self.code)
            imports = [n.name for node in ast.walk(parsed) if isinstance(node, ast.Import) for n in node.names]
            imports += [node.module for node in ast.walk(parsed) if isinstance(node, ast.ImportFrom)]
            for imp in sorted(list(set(filter(None, imports)))):
                status = "⚠️ HIGH RISK" if imp in danger_libs else "✅ SECURE"
                color = "#FF3131" if imp in danger_libs else "#00FF00"
                item = dep_tree.insert("", "end", text=f"  {imp}", values=(status,))
                dep_tree.tag_configure('tag', foreground=color)
                dep_tree.item(item, tags=('tag',))
        except: pass
        dep_tree.pack(fill="both", expand=True)

    def show_gui_and_fix(self):
        root = tk.Tk()
        root.title(f"🛡️ Audit Score: {self.risk_score}%")
        w, h = 800, 550
        ws, hs = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{w}x{h}+{ws-w-20}+{80}")
        bg_main = "#2A0000" if self.risk_score < 50 else "#0D0D0D"
        root.configure(bg=bg_main)

        toolbar = tk.Frame(root, bg="#222222", height=35)
        toolbar.pack(side="top", fill="x")
        tk.Button(toolbar, text="📦 DEPENDENCY MAP", command=self.show_dependency_map, bg="#222222", fg="#00FF00", relief="flat", font=("Arial", 8)).pack(side="left", padx=5)
        tk.Button(toolbar, text="⚙️ SETTINGS", command=self.open_settings, bg="#222222", fg="#FFD700", relief="flat", font=("Arial", 8)).pack(side="left", padx=5)

        lbl = tk.Label(root, text=f"SECURITY RISK SCORE: {self.risk_score}%", bg=bg_main, fg="#FF3131" if self.risk_score < 50 else "#00FF00", font=("Arial", 10, "bold"))
        lbl.pack(pady=5)

        paned = tk.PanedWindow(root, orient="horizontal", bg=bg_main, sashwidth=2)
        paned.pack(fill="both", expand=True, padx=5, pady=5)

        table_frame = tk.Frame(paned, bg=bg_main)
        paned.add(table_frame, width=350)
        cols = ("Line", "Vulnerability")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=50 if col=="Line" else 250)
        for v in self.vulnerabilities:
            tree.insert("", "end", values=(v["line"], v["name"]))
        tree.pack(fill="both", expand=True)

        code_text = tk.Text(paned, bg="#111111", fg="#888888", font=("Consolas", 9), wrap="none")
        code_text.insert("1.0", self.code)
        code_text.config(state="disabled")
        paned.add(code_text, width=430)

        def on_row_click(event):
            selected_item = tree.selection()
            if not selected_item: return
            item_data = tree.item(selected_item[0])
            line_no = item_data['values'][0]
            if line_no != 'N/A' and str(line_no).isdigit():
                code_text.tag_remove("highlight", "1.0", "end")
                start_pos = f"{line_no}.0"
                end_pos = f"{line_no}.end"
                code_text.tag_add("highlight", start_pos, end_pos)
                code_text.tag_config("highlight", background="#004D00", foreground="#00FF00", font=("Consolas", 10, "bold"))
                code_text.see(start_pos)

        tree.bind("<<TreeviewSelect>>", on_row_click)

        def handle_fix():
            file_name = simpledialog.askstring("Save Fix", "Enter filename:", initialvalue=f"fixed_{os.path.basename(self.file_path)}")
            if file_name:
                shutil.copy(self.file_path, self.file_path + ".bak")
                if not file_name.endswith(".py"): file_name += ".py"
                with console.status("[bold green]Generating Secure Fix & Running AST Guard..."):
                    secure_code = self.get_ai_fix()
                if secure_code:
                    self.show_diff_window(self.code, secure_code, file_name)

        btn_frame = tk.Frame(root, bg=bg_main)
        btn_frame.pack(fill="x", side="bottom", pady=10)
        tk.Button(btn_frame, text="🚀 FIX WITH AST-GUARD", command=handle_fix, bg="#008037", fg="white", font=("Arial", 9, "bold"), padx=15).pack(side="right", padx=15)
        tk.Button(btn_frame, text="CLOSE", command=root.destroy, bg="#333333", fg="white", font=("Arial", 9), padx=10).pack(side="right")
        root.mainloop()

# --- AUTO SCAN ---
import __main__

if hasattr(__main__, "__file__"):
    main_file = __main__.__file__
    # Yahan se bhi status hata diya taaki conflicts na hon
    with console.status("[bold yellow]Processing Security Audit..."):
        audit_engine = SecureGenAI(main_file).scan()
    audit_engine.show_gui_and_fix()
