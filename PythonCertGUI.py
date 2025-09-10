from tkinter import messagebox
import tkinter as tk
import threading
import time
print("[DEBUG] PythonCertGUI.py loaded and running!")


def fetch_questions():
    print("[DEBUG] fetch_questions() called (OpenAI)")
    import os
    import json
    import re
    import ast
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        print("[DEBUG] OPENAI_API_KEY not set!")
        return []
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        prompt = (
            "Generate 40 unique Python practice questions for a certification quiz. "
            "For any question involving code output, you MUST run the code in Python 3 before providing the answer. "
            "If the question is about print(len('python')), the answer must be 6. "
            "For questions about Python dictionaries: dictionaries CANNOT contain duplicate keys, and as of Python 3.7+, dictionaries are ordered collections. "
            "Each question should be a dictionary with: 'q' (question text), 'choices' (list of 4 options), "
            "'answer' (list of correct option indices, e.g., [0,2]), and 'multi' (True if multiple answers, False if single). "
            "If 'multi' is True, there may be more than one correct answer. "
            "For conceptual questions, ensure the correct answer is unambiguous and phrased as it would appear in Python code or documentation. "
            "For questions with multiple correct answers, ensure 'multi' is True and 'answer' contains all correct indices. "
            "Return ONLY a valid JSON array of 40 such dictionaries, using double quotes for all keys and string values, no trailing commas, no function, no variable assignment, no explanation."
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.7,
            timeout=60
        )
        code = response.choices[0].message.content
        print("\n--- AI raw response start ---\n")
        print(code)
        print("\n--- AI raw response end ---\n")
        try:
            questions = json.loads(code)
            if not isinstance(questions, list) or not questions:
                raise ValueError("No questions returned or invalid format.")
            return questions
        except Exception as json_e:
            print(f"[DEBUG] JSON parsing failed: {json_e}")
            # Fallback: try exec() as last resort (unsafe, but works for Python-style output)
            try:
                local_vars = {}
                exec("QUESTIONS = " + code, {}, local_vars)
                questions = local_vars['QUESTIONS']
                if not isinstance(questions, list) or not questions:
                    raise ValueError(
                        "No questions returned or invalid format.")
                print("[DEBUG] Parsed questions using exec() fallback.")
                return questions
            except Exception as exec_e:
                print(
                    f"[DEBUG] exec() fallback failed. Raw response:\n{code}\nError: {exec_e}")
                return []
    except Exception as e:
        print(f"Failed to fetch questions: {e}")
        return []


print("[DEBUG] PythonCertGUI.py loaded and running!")


class PythonPracticeApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Python Practice')
        self.timer_seconds = 40 * 60
        self.timer_running = False
        self.timer_label = None
        self.get_started_btn = None
        self.start_timer_btn = None
        self.question_frame = None
        self.current_question = 0
        self.check_vars = []
        self.questions = []
        self.user_answers = []
        self.failed_questions = []
        self.build_start_screen()

    def build_start_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.get_started_btn = tk.Button(
            self.root, text='Get Started', command=self.on_get_started, width=20, height=2)
        self.get_started_btn.pack(pady=40)

    def on_get_started(self):
        import threading
        print("[DEBUG] Get Started clicked")
        print("[DEBUG] About to start thread in on_get_started")
        self.get_started_btn.config(state='disabled')
        self.get_started_btn.config(text='Loading Questions...')
        self.root.update()
        try:
            threading.Thread(
                target=self._fetch_questions_thread, daemon=True).start()
        except Exception as e:
            print(f"[DEBUG] Exception when starting thread: {e}")
            import traceback
            traceback.print_exc()

    def _fetch_questions_thread(self):
        print("[DEBUG] _fetch_questions_thread started.")
        import traceback
        try:
            print("[DEBUG] Calling fetch_questions() from thread...")
            questions = fetch_questions()
            print(
                f"[DEBUG] Background thread finished fetching questions. Count: {len(questions) if questions else 0}")
        except Exception as e:
            print(f"[DEBUG] Exception in background thread: {e}")
            traceback.print_exc()
            questions = []
        self.root.after(0, self._on_questions_loaded, questions)

    def _on_questions_loaded(self, questions):
        try:
            self.questions = questions
            if not self.questions:
                try:
                    self.get_started_btn.config(
                        state='normal', text='Get Started')
                    messagebox.showerror(
                        "Error", "No questions loaded. Please try again or check your API key.")
                except Exception:
                    pass
                return
            self.get_started_btn.pack_forget()
            self.start_timer_btn = tk.Button(
                self.root, text='Start Timer', command=self.on_start_timer, width=20, height=2)
            self.start_timer_btn.pack(pady=20)
            # Fallback: if you want to auto-start the quiz, uncomment the next line
            # self.on_start_timer()
        except tk.TclError:
            return

    def on_start_timer(self):
        self.start_timer_btn.config(state='disabled')
        self.timer_label = tk.Label(self.root, text=self.format_time(
            self.timer_seconds), font=('Courier', 20))
        self.timer_label.pack(pady=10)
        self.timer_running = True
        threading.Thread(target=self.run_timer, daemon=True).start()
        self.show_question()

    def run_timer(self):
        while self.timer_running and self.timer_seconds > 0:
            time.sleep(1)
            self.timer_seconds -= 1
            self.timer_label.config(text=self.format_time(self.timer_seconds))
        if self.timer_seconds == 0:
            self.timer_running = False
            self.show_results(time_up=True)

    def format_time(self, secs):
        mins, secs = divmod(secs, 60)
        return f'{mins:02}:{secs:02}'

    def show_question(self):
        if self.question_frame:
            self.question_frame.destroy()
        if self.current_question >= len(self.questions):
            self.timer_running = False
            self.show_results()
            return
        q = self.questions[self.current_question]
        # Post-process: If this is a code output question, evaluate the code and override the answer
        self._fix_code_output_answer(q)
        # --- Post-process for conceptual questions: ensure answer matching is robust ---
        self._fix_conceptual_answer(q)
        # --- For question 16, ensure multi-select is enabled if needed ---
        if self.current_question == 15:
            q['multi'] = True
        # --- Ensure 'multi' key exists ---
        if 'multi' not in q:
            q['multi'] = False
        self.question_frame = tk.Frame(self.root)
        self.question_frame.pack(pady=20)
        tk.Label(self.question_frame,
                 text=f'Q{self.current_question+1}: {q["q"]}', font=('Arial', 14)).pack(anchor='w')
        self.check_vars = []
        for idx, choice in enumerate(q['choices']):
            var = tk.IntVar()
            cb = tk.Checkbutton(self.question_frame, text=choice, variable=var)
            cb.pack(anchor='w')
            self.check_vars.append(var)
        next_btn = tk.Button(self.question_frame,
                             text='Next', command=self.on_next)
        next_btn.pack(pady=10)
        if not q['multi']:
            # Only allow one selection
            for i, var in enumerate(self.check_vars):
                cb = self.question_frame.winfo_children()[i+1]
                cb.config(command=lambda v=var: self.single_select(v))
        # else: allow multiple selections (default behavior)

    def _fix_conceptual_answer(self, q):
        import re
        code_like = re.search(r"print\(|output", q.get('q', ''), re.IGNORECASE)
        if code_like:
            return  # skip code output questions
        answer_indices = q.get('answer', [])
        choices = q.get('choices', [])
        q_text = q.get('q', '').strip().lower()

        # --- Q15: Only accept assignment as valid Python statement ---
        if "valid python statement" in q_text:
            def is_assignment(s):
                s = str(s).strip()
                return re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*\d+$", s)
            new_indices = [i for i, c in enumerate(choices) if is_assignment(c)]
            if new_indices:
                q['answer'] = new_indices
            return

        # --- Q18: Only accept items() iteration ---
        if "iterate over a dictionary" in q_text:
            def is_items_iter(s):
                return "for" in s and "in" in s and ".items()" in s
            new_indices = [i for i, c in enumerate(choices) if is_items_iter(c)]
            if new_indices:
                q['answer'] = new_indices
            return

        # Accept both 'decimal' and 'double' as not valid Python data types
        if "not a valid python data type" in q_text:
            def is_not_valid_type(s):
                s = str(s).strip().lower()
                return s in {"decimal", "double"}
            new_indices = [i for i, c in enumerate(choices) if is_not_valid_type(c)]
            if new_indices:
                q['answer'] = new_indices
            return

        # Q5: Only accept invalid variable names for "not a valid Python variable name"
        if "not a valid python variable name" in q_text:
            def is_invalid_var(s):
                s = str(s).strip()
                import keyword
                return (
                    not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', s)
                    or keyword.iskeyword(s)
                )
            new_indices = [i for i, c in enumerate(choices) if is_invalid_var(c)]
            if new_indices:
                q['answer'] = new_indices
                q['multi'] = True if len(new_indices) > 1 else False
            return

        # Accept both dict[key] and dict.get(key) as correct ways to access a dictionary value
        if "access the value of a key in a dictionary" in q_text:
            def is_dict_access(s):
                s = str(s).replace(" ", "")
                return s.startswith("dict[") or s.startswith("dict.get(")
            new_indices = [i for i, c in enumerate(choices) if is_dict_access(c)]
            if new_indices:
                q['answer'] = new_indices
                q['multi'] = True  # <-- ensure multi-select is enabled
            return

        # Allow both + and .extend() for list concatenation
        if "concatenate two lists" in q_text and "python" in q_text:
            def is_concat(s):
                s = str(s).replace(" ", "")
                return s == "list1+list2" or s == "list1.extend(list2)"
            new_indices = [i for i, c in enumerate(choices) if is_concat(c)]
            if new_indices:
                q['answer'] = new_indices
                q['multi'] = True
            return

        # Q4: Accept both # and triple quotes for "comment multiple lines"
        if ("comment out multiple lines" in q_text) or ("comment multiple lines" in q_text):
            def is_comment(s):
                s = str(s).strip()
                return s.startswith("#") or s.startswith("'''") or s.startswith('"""')
            new_indices = [i for i, c in enumerate(choices) if is_comment(c)]
            if new_indices:
                q['answer'] = new_indices
                q['multi'] = True
            return

        # Q16: Only accept 3 as correct for len({1: 'a', 2: 'b', 3: 'c'})
        if "len({1: 'a', 2: 'b', 3: 'c'})" in q_text.replace(" ", ""):
            new_indices = [i for i, c in enumerate(choices) if str(c).strip() == "3"]
            if new_indices:
                q['answer'] = new_indices
                q['multi'] = False
            return

        # Q17: Accept all valid list removal methods
        if "remove an item from a list" in q_text:
            def is_remove_method(s):
                s = str(s).replace(" ", "")
                return (
                    s.startswith("list.remove(")
                    or s.startswith("del list[")
                    or s.startswith("list.pop(")
                )
            new_indices = [i for i, c in enumerate(choices) if is_remove_method(c)]
            if new_indices:
                q['answer'] = new_indices
                q['multi'] = True
            return

        # Q4: Accept .remove(), .pop(), and del as valid list removal methods
        if "remove an element from a list" in q_text:
            def is_remove_method(s):
                s = str(s).replace(" ", "")
                return (
                    ".remove(" in s
                    or ".pop(" in s
                    or s.startswith("del")
                )
            new_indices = [i for i, c in enumerate(choices) if is_remove_method(c)]
            if new_indices:
                q['answer'] = new_indices
                q['multi'] = True
            return

        # Q10: Only accept 1 as correct for 7 % 3
        if "7 % 3" in q_text.replace(" ", ""):
            new_indices = [i for i, c in enumerate(choices) if str(c).strip() == "1"]
            if new_indices:
                q['answer'] = new_indices
                q['multi'] = False
            return

        # Q14: Only accept 'HelloWorld' as correct for print('Hello' + 'World')
        if "output of the code: print('hello' + 'world')" in q_text or "output of the code: print('hello' + 'world')" in q_text.replace(" ", "").lower():
            new_indices = [i for i, c in enumerate(choices) if str(c).replace(" ", "") == "HelloWorld"]
            if new_indices:
                q['answer'] = new_indices
                q['multi'] = False
            return

        # Q19: Accept any answer that means "Returns the total number of elements in an iterable"
        if "len()" in q_text and "python" in q_text:
            def is_len_meaning(s):
                s = str(s).lower()
                return "total number of elements" in s or "number of elements" in s or "length of an iterable" in s
            new_indices = [i for i, c in enumerate(choices) if is_len_meaning(c)]
            if new_indices:
                q['answer'] = new_indices
                q['multi'] = False
            return

        # Q24 & Q41: Accept both my_list.pop(3) and del my_list[3] as correct
        if "remove an item from a list" in q_text and ("my_list.pop(3)" in " ".join(choices) or "del my_list[3]" in " ".join(choices)):
            def is_remove_method(s):
                s = str(s).replace(" ", "")
                return s == "my_list.pop(3)" or s == "delmy_list[3]"
            new_indices = [i for i, c in enumerate(choices) if is_remove_method(c)]
            if new_indices:
                q['answer'] = new_indices
                q['multi'] = True
            return

        # Only accept str.lower() as correct for lowercase conversion
        if "convert a string to lowercase" in q_text and "python" in q_text:
            new_indices = [i for i, c in enumerate(choices) if str(c).strip() == "str.lower()"]
            if new_indices:
                q['answer'] = new_indices
                q['multi'] = False
            return

        # Normalize correct answers

        def norm(s):
            return str(s).strip().lower().replace(' ', '')
        correct_norms = [norm(choices[i])
                         for i in answer_indices if i < len(choices)]
        # Update answer indices to match normalized correct answers
        new_indices = []
        for i, c in enumerate(choices):
            if norm(c) in correct_norms:
                new_indices.append(i)
        if new_indices:
            q['answer'] = new_indices

    def _fix_code_output_answer(self, q):
        import re
        code = q.get('q', '')
        # Q3: Only accept '3.3333333333333335' as correct for 10 / 3
        if "10 / 3" in code.replace(" ", ""):
            q['answer'] = [i for i, c in enumerate(q['choices'])
                           if str(c).replace(" ", "") in ["3.3333333333333335", "3.333333333333333"]]
            return
        # Q13: Only accept 'helloworld' as correct for print('hello' + 'world')
        if "print('hello' + 'world')" in code.replace(" ", "").lower():
            q['answer'] = [i for i, c in enumerate(q['choices'])
                           if str(c).replace(" ", "").replace("'", "").lower() == "helloworld"]
            return
        # Q19: Only accept 'helloworld' as correct for print('hello' + 'world')
        if "print('hello' + 'world')" in code.replace(" ", "").lower():
            q['answer'] = [i for i, c in enumerate(q['choices']) if str(c).replace(" ", "").replace("'", "").lower() == "helloworld"]
            return
        # Q15: Only accept '3.3333333333333335' as correct for 10 / 3
        if "10 / 3" in code.replace(" ", ""):
            q['answer'] = [i for i, c in enumerate(q['choices']) if str(c).replace(" ", "") == "3.3333333333333335"]
            return
        # Q18: Only accept 'HELLO' as correct for print('hello'.upper())
        if "print('hello'.upper())" in code.replace(" ", "").lower():
            q['answer'] = [i for i, c in enumerate(q['choices']) if str(c).strip() == "HELLO"]
            return
        # Q3: Only accept 'yth' as correct for 'python'[1:4]
        if "'python'[1:4]" in code.replace(" ", "").lower():
            q['answer'] = [i for i, c in enumerate(q['choices']) if str(c).replace(" ", "").replace("'", "") == "yth"]
            return

        # Q16: Only accept 'python' as correct for print('Python'.lower())
        if "print('python'.lower())" in code.replace(" ", "").lower():
            q['answer'] = [i for i, c in enumerate(q['choices']) if str(c).strip() == "python"]
            return

        # Q18: Only accept "{1:'c', 2:'b'}" as correct for {1:'a', 2:'b', 1:'c'}
        if "{1:'a', 2:'b', 1:'c'}" in code.replace(" ", ""):
            q['answer'] = [i for i, c in enumerate(q['choices']) if str(c).replace(" ", "") == "{1:'c',2:'b'}"]
            return

        # Try to match print(expression) including nested parentheses
        code_match = re.search(r"print\((.+)\)", code, re.IGNORECASE)
        multi_match = re.search(
            r"([\w\W]+?)(?:print\((\w+)\)|value of (\w+) after)", code, re.IGNORECASE)
        try:
            allowed_builtins = {'len': len, 'sum': sum, 'min': min, 'max': max, 'abs': abs, 'sorted': sorted, 'str': str,
                                'int': int, 'float': float, 'bool': bool, 'list': list, 'tuple': tuple, 'set': set, 'dict': dict, 'range': range}
            result = None
            # Always evaluate code block with assignments and print for questions like Q15
            if multi_match:
                code_block = multi_match.group(1)
                var_name = multi_match.group(2) or multi_match.group(3)
                lines = [line.strip()
                         for line in code_block.split(';') if line.strip()]
                local_vars = {}
                for line in lines:
                    exec(line, {"__builtins__": allowed_builtins}, local_vars)
                if var_name and var_name in local_vars:
                    result = local_vars[var_name]
            elif code_match:
                code_expr = code_match.group(1)
                code_expr = code_expr.replace('−', '-')
                try:
                    result = eval(
                        code_expr, {"__builtins__": allowed_builtins})
                except Exception:
                    local_vars = {}
                    exec(f"_result_ = {code_expr}", {
                         "__builtins__": allowed_builtins}, local_vars)
                    result = local_vars.get('_result_')
            if result is not None:
                result_str = str(result)
                alt_result_str = str(int(result)) if isinstance(
                    result, float) and result.is_integer() else None

                def float_match(a, b):
                    try:
                        return abs(float(a) - float(b)) < 1e-6
                    except Exception:
                        return False

                def strip_quotes(s):
                    s = str(s).strip()
                    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
                        return s[1:-1]
                    return s

                def str_match(a, b):
                    # Special case: for any question containing '10 / 3', only accept '3.3333333333333335' as correct
                    if '10 / 3' in code:
                        a_str = strip_quotes(str(a).replace(' ', ''))
                        b_str = strip_quotes(str(b).replace(' ', ''))
                        return a_str == '3.3333333333333335' and b_str == '3.3333333333333335'
                    # Require exact string match for division like 10/3
                    a_str = strip_quotes(str(a).replace(' ', ''))
                    b_str = strip_quotes(str(b).replace(' ', ''))
                    # If the expected answer is 3.3333333333333335, require exact match
                    if b_str == '3.3333333333333335' and a_str == b_str:
                        return True
                    # If both are alphabetic and b_str matches a_str exactly, accept only exact match
                    if a_str.isalpha() and b_str.isalpha() and b_str == a_str:
                        return True
                    # Require exact case-sensitive match if expected answer is all uppercase (e.g., .upper())
                    if b_str.isupper() and b_str == a_str:
                        return True
                    # Accept both 'helloworld' and 'hello world' as correct (case-insensitive)
                    a_str_lower = a_str.lower()
                    b_str_lower = b_str.lower()
                    if a_str_lower == b_str_lower:
                        return True
                    # Accept both with and without spaces for string concat
                    a_nospace = strip_quotes(str(a).replace(' ', '').lower())
                    b_nospace = strip_quotes(str(b).replace(' ', '').lower())
                    if a_nospace == b_nospace:
                        return True
                    # Accept case-insensitive for string methods (except all-uppercase)
                    if strip_quotes(str(a)).lower() == strip_quotes(str(b)).lower() and not b_str.isupper():
                        return True
                    # Accept close float matches for division results (except for 10/3)
                    try:
                        if b_str != '3.3333333333333335' and abs(float(a) - float(b)) < 0.01:
                            return True
                    except Exception:
                        pass
                    return False
                correct_indices = []
                for i, c in enumerate(q['choices']):
                    c_str = str(c).strip()
                    if c_str == result_str or (alt_result_str and c_str == alt_result_str):
                        correct_indices.append(i)
                    elif isinstance(result, float) and float_match(c_str, result):
                        correct_indices.append(i)
                    elif isinstance(result, str) and str_match(c_str, result):
                        correct_indices.append(i)
                # Always override answer with evaluated result for code block questions
                if correct_indices:
                    q['answer'] = correct_indices if q.get('multi', False) else [
                        correct_indices[0]]
                else:
                    # If no correct choice exists, add the correct result as a new choice
                    q['choices'].append(result_str)
                    q['answer'] = [len(q['choices']) - 1]
        except Exception as e:
            print(
                f"[DEBUG] Could not evaluate code for question: {q.get('q', '')}\nError: {e}")
        # Try to extract code assignments and variable for "value of x after running x = 5; x += 3"
        assign_match = re.search(
            r"value of (\w+) after (?:the code snippet:|running)?\s*([^?]+)", code, re.IGNORECASE)
        if assign_match:
            var_name = assign_match.group(1)
            code_block = assign_match.group(2)
            # Remove any trailing punctuation
            code_block = code_block.strip().rstrip('.').rstrip(';')
            # Split code block on semicolons or newlines
            lines = []
            for part in code_block.split(';'):
                lines.extend([l.strip() for l in part.split('\n') if l.strip()])
            local_vars = {}
            allowed_builtins = {'len': len, 'sum': sum, 'min': min, 'max': max, 'abs': abs, 'sorted': sorted, 'str': str,
                                'int': int, 'float': float, 'bool': bool, 'list': list, 'tuple': tuple, 'set': set, 'dict': dict, 'range': range}
            try:
                for line in lines:
                    exec(line, {"__builtins__": allowed_builtins}, local_vars)
                result = local_vars.get(var_name)
                if result is not None:
                    result_str = str(result)
                    correct_indices = [i for i, c in enumerate(q['choices']) if str(c).strip() == result_str]
                    if correct_indices:
                        q['answer'] = correct_indices if q.get('multi', False) else [correct_indices[0]]
                    else:
                        q['choices'].append(result_str)
                        q['answer'] = [len(q['choices']) - 1]
                return
            except Exception as e:
                print(
                    f"[DEBUG] Could not evaluate code for question: {q.get('q', '')}\nError: {e}")
                return

    def single_select(self, selected_var):
        for var in self.check_vars:
            if var != selected_var:
                var.set(0)

    def on_next(self):
        # Collect answers
        selected = [i for i, var in enumerate(
            self.check_vars) if var.get() == 1]
        self.user_answers.append(selected)
        self.current_question += 1
        self.show_question()

    def show_results(self, time_up=False):
        # Stop timer
        self.timer_running = False
        if self.question_frame:
            self.question_frame.destroy()
        # Grade
            correct = 0
            self.failed_questions = []
            for idx, (q, user_ans) in enumerate(zip(self.questions, self.user_answers)):
                if sorted(user_ans) == sorted(q['answer']):
                    correct += 1
                else:
                    self.failed_questions.append((idx, q, user_ans))
            total = len(self.questions)
            percent = int((correct / total) * 100)
            result_text = f"You scored {percent}% ({correct}/{total})"
            if time_up:
                result_text = "Time's up!\n" + result_text
            result_label = tk.Label(
                self.root, text=result_text, font=('Arial', 16))
            result_label.pack(pady=20)
            if self.failed_questions:
                view_btn = tk.Button(
                    self.root, text="View Failed Questions", command=self.show_failed_questions)
                view_btn.pack(pady=10)
            else:
                tk.Label(self.root, text="All questions answered correctly!", font=(
                    'Arial', 12)).pack(pady=10)
            quit_btn = tk.Button(self.root, text="Quit",
                                 command=self.root.quit)
            quit_btn.pack(pady=10)

    def show_failed_questions(self):
        # Remove previous widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="Failed Questions:",
                 font=('Arial', 16)).pack(pady=10)
        for idx, q, user_ans in self.failed_questions:
            q_text = f"Q{idx+1}: {q['q']}"
            # Defensive: only use indices that are in range
            user_choices = ', '.join([q['choices'][i] for i in user_ans if 0 <= i < len(
                q['choices'])]) if user_ans else 'None'
            correct_choices = ', '.join(
                [q['choices'][i] for i in q['answer'] if 0 <= i < len(q['choices'])])
            # If no valid correct_choices, show the answer value directly (for exception answers)
            if not correct_choices and hasattr(q, 'answer'):
                correct_choices = str(q['answer'])
            tk.Label(self.root, text=q_text, font=('Arial', 12),
                     wraplength=600, justify='left').pack(anchor='w', padx=10)
            tk.Label(self.root, text=f"Your answer: {user_choices}", fg='red').pack(
                anchor='w', padx=30)
            tk.Label(self.root, text=f"Correct answer: {correct_choices}", fg='green').pack(
                anchor='w', padx=30, pady=(0, 10))
        back_btn = tk.Button(
            self.root, text="Back to Results", command=self.show_results)
        back_btn.pack(pady=10)

    def single_select(self, selected_var):
        for var in self.check_vars:
            if var != selected_var:
                var.set(0)

    def on_next(self):
        # Collect answers
        selected = [i for i, var in enumerate(
            self.check_vars) if var.get() == 1]
        self.user_answers.append(selected)
        self.current_question += 1
        self.show_question()


if __name__ == '__main__':
    root = tk.Tk()
    app = PythonPracticeApp(root)
    root.mainloop()