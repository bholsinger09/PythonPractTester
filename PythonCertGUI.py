import tkinter as tk
from tkinter import messagebox
import time
import threading
import openai
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

def fetch_questions():
    prompt = (
        "Generate 44 unique Python practice questions for a certification quiz. "
        "Each question should be a dictionary with: 'q' (question text), 'choices' (list of 4 options), "
        "'answer' (list of correct option indices, e.g., [0,2]), and 'multi' (True if multiple answers, False if single). "
        "Return a Python list of 44 such dictionaries."
    )
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.7
        )
        code = response.choices[0].message.content
        # Extract the list from the response
        local_vars = {}
        exec("QUESTIONS = " + code, {}, local_vars)
        return local_vars['QUESTIONS']
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch questions: {e}")
        return []


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
        self.get_started_btn = tk.Button(self.root, text='Get Started', command=self.on_get_started, width=20, height=2)
        self.get_started_btn.pack(pady=40)

    def on_get_started(self):
        self.get_started_btn.config(state='disabled')
        self.get_started_btn.config(text='Loading Questions...')
        self.root.update()
        self.questions = fetch_questions()
        if not self.questions:
            self.root.quit()
            return
        self.get_started_btn.pack_forget()
        self.start_timer_btn = tk.Button(self.root, text='Start Timer', command=self.on_start_timer, width=20, height=2)
        self.start_timer_btn.pack(pady=20)

    def on_start_timer(self):
        self.start_timer_btn.config(state='disabled')
        self.timer_label = tk.Label(self.root, text=self.format_time(self.timer_seconds), font=('Courier', 20))
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
        self.question_frame = tk.Frame(self.root)
        self.question_frame.pack(pady=20)
        tk.Label(self.question_frame, text=f'Q{self.current_question+1}: {q["q"]}', font=('Arial', 14)).pack(anchor='w')
        self.check_vars = []
        for idx, choice in enumerate(q['choices']):
            var = tk.IntVar()
            cb = tk.Checkbutton(self.question_frame, text=choice, variable=var)
            cb.pack(anchor='w')
            self.check_vars.append(var)
        next_btn = tk.Button(self.question_frame, text='Next', command=self.on_next)
        next_btn.pack(pady=10)
        if not q['multi']:
            # Only allow one selection
            for i, var in enumerate(self.check_vars):
                cb = self.question_frame.winfo_children()[i+1]
                cb.config(command=lambda v=var: self.single_select(v))

    def single_select(self, selected_var):
        for var in self.check_vars:
            if var != selected_var:
                var.set(0)

    def on_next(self):
        # Collect answers
        selected = [i for i, var in enumerate(self.check_vars) if var.get() == 1]
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
        result_label = tk.Label(self.root, text=result_text, font=('Arial', 16))
        result_label.pack(pady=20)
        if self.failed_questions:
            view_btn = tk.Button(self.root, text="View Failed Questions", command=self.show_failed_questions)
            view_btn.pack(pady=10)
        else:
            tk.Label(self.root, text="All questions answered correctly!", font=('Arial', 12)).pack(pady=10)
        quit_btn = tk.Button(self.root, text="Quit", command=self.root.quit)
        quit_btn.pack(pady=10)

    def show_failed_questions(self):
        # Remove previous widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="Failed Questions:", font=('Arial', 16)).pack(pady=10)
        for idx, q, user_ans in self.failed_questions:
            q_text = f"Q{idx+1}: {q['q']}"
            user_choices = ', '.join([q['choices'][i] for i in user_ans]) if user_ans else 'None'
            correct_choices = ', '.join([q['choices'][i] for i in q['answer']])
            tk.Label(self.root, text=q_text, font=('Arial', 12), wraplength=600, justify='left').pack(anchor='w', padx=10)
            tk.Label(self.root, text=f"Your answer: {user_choices}", fg='red').pack(anchor='w', padx=30)
            tk.Label(self.root, text=f"Correct answer: {correct_choices}", fg='green').pack(anchor='w', padx=30, pady=(0,10))
        back_btn = tk.Button(self.root, text="Back to Results", command=self.show_results)
        back_btn.pack(pady=10)

if __name__ == '__main__':
    root = tk.Tk()
    app = PythonPracticeApp(root)
    root.mainloop()
