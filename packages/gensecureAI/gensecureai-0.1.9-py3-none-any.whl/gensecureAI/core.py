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
DEFAULT_GROQ_API_KEY ="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"
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

    def scan(self):
        tree = ast.parse(self.code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.BinOp, ast.JoinedStr)):
                code_snippet = ast.unparse(node).upper()
                if any(k in code_snippet for k in ["SELECT", "INSERT", "UPDATE", "DELETE", "DROP"]):
                    self._add_v(node, "SQL Injection", "CRITICAL", "CWE-89")
            
            if isinstance(node, ast.Call):
                func_name = ast.unparse(node.func)
                if any(x in func_name for x in ["os.system", "os.popen", "subprocess.call"]):
                    self._add_v(node, "OS Command Injection", "CRITICAL", "CWE-78")
                if func_name in ["eval", "exec", "compile"]:
                    self._add_v(node, "Code Injection", "CRITICAL", "CWE-94")

            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        t_name = target.id.upper()
                        if any(s in t_name for s in ["API_KEY", "SECRET", "PASSWORD", "TOKEN", "PWD"]):
                            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                                self._add_v(node, "Hardcoded Secret", "CRITICAL", "CWE-798")

        try:
            result = subprocess.run(["pip", "list", "--outdated"], capture_output=True, text=True)
            if result.stdout:
                self.vulnerabilities.append({"line": "System", "name": "Outdated Dependencies", "risk": "MEDIUM"})
        except: pass

        critical_count = len([v for v in self.vulnerabilities if v.get("risk") == "CRITICAL"])
        self.risk_score = max(0, 100 - (critical_count * 20) - (len(self.vulnerabilities) * 5))
        
        self.generate_html_report()
        return self

    def _add_v(self, node, name, risk, cwe):
        self.vulnerabilities.append({
            "line": getattr(node, 'lineno', 'N/A'),
            "name": name, "risk": risk, "cwe": cwe
        })

    def open_settings(self):
        new_key = simpledialog.askstring("Settings", "Update Groq API Key:", initialvalue=self.current_key)
        if new_key:
            try:
                test_client = Groq(api_key=new_key)
                test_client.models.list() 
                self.current_key = new_key
                save_api_key(new_key)
                messagebox.showinfo("Success", "API Key validated and saved.")
            except Exception as e:
                messagebox.showerror("Validation Failed", f"Invalid Key or Limit Reached: {e}")

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

    def generate_html_report(self):
        report_path = "security_report.html"
        html = f"<html><body style='font-family:sans-serif;background:#f4f4f4;'><h1>Security Audit: {os.path.basename(self.file_path)}</h1>"
        html += f"<h3>Risk Score: {self.risk_score}%</h3><table border='1'><tr><th>Line</th><th>Issue</th><th>Risk</th></tr>"
        for v in self.vulnerabilities:
            html += f"<tr><td>{v['line']}</td><td>{v['name']}</td><td>{v.get('risk','N/A')}</td></tr>"
        html += "</table></body></html>"
        with open(report_path, "w") as f: f.write(html)

    def get_ai_fix(self):
        try:
            client = Groq(api_key=self.current_key)
            prompt = f"""
        [ROLE]
        You are a Principal Application Security Engineer, Python Language Expert,
        and Secure Code Reviewer with real-world production experience.

        [OBJECTIVE]
        You are given Python source code that may contain security vulnerabilities.
        Your task is to produce a corrected version that is:
        - Secure
        - Functionally equivalent
        - Production-grade
        - Readable and maintainable

        [STRICT RULES — READ CAREFULLY]
        1. DO NOT remove or break existing functionality.
        2. DO NOT introduce placeholders or pseudocode.
        3. DO NOT change public APIs, function names, or return values unless required for security.
        4. DO NOT add new external dependencies.
        5. DO NOT assume missing context.
        6. DO NOT add comments explaining security theory.
        7. DO NOT output markdown, explanations, or text outside pure Python code.

        [SECURITY HARDENING REQUIREMENTS]
        Apply fixes ONLY where applicable:
        - Replace SQL string concatenation with parameterized queries.
        - Replace os.system / shell=True with subprocess.run(list, shell=False).
        - Replace eval / exec / compile with safe alternatives or remove if unnecessary.
        - Replace hardcoded secrets ONLY if safer retrieval exists in the same codebase.
        - Validate file paths using pathlib.Path to prevent traversal.
        - Ensure subprocess arguments are not user-injected.

        [QUALITY REQUIREMENTS]
        - Code must pass ast.parse() without errors.
        - Follow PEP8 style.
-        No dead code or unused imports.
        - Keep logic minimal and explicit.

        [OUTPUT FORMAT — ABSOLUTE]
        Return ONLY the corrected Python source code.
        NO explanations.
        NO markdown.
        NO code fences.

        [INPUT CODE]
        {self.code}
            """
            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=[
                    {"role": "system", "content": "You are a world-class Python security hardening agent."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            fixed_code = response.choices[0].message.content
            if not fixed_code: return ""
            fixed_code = fixed_code.strip()
            if "```" in fixed_code:
                if "```python" in fixed_code:
                    fixed_code = fixed_code.split("```python")[1].split("```")[0].strip()
                else:
                    fixed_code = fixed_code.split("```")[1].split("```")[0].strip()
            return fixed_code
        except Exception as e:
            err = str(e).lower()
            if any(x in err for x in ["limit", "rate", "unauthorized", "api_key"]):
                new_key = simpledialog.askstring("API Key Required", "Enter a new Groq API Key:")
                if new_key:
                    self.current_key = new_key
                    save_api_key(new_key)
                    return self.get_ai_fix()
            return ""

    def show_diff_window(self, old_code, new_code, output_file):
        diff_win = tk.Toplevel()
        diff_win.title("Vulnerability Comparison (Diff View)")
        diff_win.geometry("900x600")
        diff_win.configure(bg="#0D0D0D")

        # Instructions
        tk.Label(diff_win, text="🔴 RED: Removed/Insecure  |  🟢 GREEN: Added/Secure", 
                 bg="#0D0D0D", fg="white", font=("Arial", 10, "bold")).pack(pady=5)

        txt_frame = tk.Frame(diff_win, bg="#0D0D0D")
        txt_frame.pack(fill="both", expand=True, padx=10, pady=5)

        diff_text = tk.Text(txt_frame, bg="#111111", fg="white", font=("Consolas", 10))
        diff_text.pack(side="left", fill="both", expand=True)
        
        scroll = tk.Scrollbar(txt_frame, command=diff_text.yview)
        scroll.pack(side="right", fill="y")
        diff_text.config(yscrollcommand=scroll.set)

        # Generate Diff
        diff = difflib.ndiff(old_code.splitlines(), new_code.splitlines())
        for line in diff:
            if line.startswith('- '):
                diff_text.insert("end", line + "\n", "removed")
            elif line.startswith('+ '):
                diff_text.insert("end", line + "\n", "added")
            elif line.startswith('? '):
                continue
            else:
                diff_text.insert("end", line + "\n")

        diff_text.tag_config("removed", background="#4B0000", foreground="#FFCCCC")
        diff_text.tag_config("added", background="#003300", foreground="#CCFFCC")
        diff_text.config(state="disabled")

        def final_save():
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(new_code)
            messagebox.showinfo("Success", f"Fixed code saved to {output_file}")
            diff_win.destroy()

        btn_f = tk.Frame(diff_win, bg="#0D0D0D")
        btn_f.pack(fill="x", side="bottom", pady=10)
        tk.Button(btn_f, text="CONFIRM & SAVE FIXED CODE", command=final_save, bg="#008037", fg="white", font=("Arial", 10, "bold"), padx=20).pack(pady=5)

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

        btn_frame = tk.Frame(root, bg=bg_main)
        btn_frame.pack(fill="x", side="bottom", pady=10)

        def handle_fix():
            file_name = simpledialog.askstring("Save Fix", "Enter filename:", 
                                             initialvalue=f"fixed_{os.path.basename(self.file_path)}")
            if file_name:
                shutil.copy(self.file_path, self.file_path + ".bak")
                if not file_name.endswith(".py"): file_name += ".py"
                
                # 'with console.status' hata diya taaki Rich library error na de
                secure_code = self.get_ai_fix() 
                
                if secure_code:
                    self.show_diff_window(self.code, secure_code, file_name)
                else:
                    messagebox.showerror("Error", "Could not generate fix. Check API key.")

        btn_frame = tk.Frame(root, bg=bg_main)
        btn_frame.pack(fill="x", side="bottom", pady=10)
        tk.Button(btn_frame, text="🚀 FIX & BACKUP", command=handle_fix, bg="#008037", fg="white", font=("Arial", 9, "bold"), padx=15).pack(side="right", padx=15)
        tk.Button(btn_frame, text="CLOSE", command=root.destroy, bg="#333333", fg="white", font=("Arial", 9), padx=10).pack(side="right")
        root.mainloop()

# --- AUTO SCAN ON IMPORT ---
# --- core.py ka aakhri hissa ---
import __main__

if hasattr(__main__, "__file__"):
    main_file = __main__.__file__
    # Yahan se bhi status hata diya taaki conflicts na hon
    with console.status("[bold yellow]Processing Security Audit..."):
        audit_engine = SecureGenAI(main_file).scan()
    audit_engine.show_gui_and_fix()



