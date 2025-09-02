import time

def clear_screen():
	print("\033[H\033[J", end="")

def get_started():
	clear_screen()
	print("Welcome to pythonPractice!\n")
	input("Press Enter to Get Started...")
	return True

def start_timer():
	clear_screen()
	print("Timer started! (Press Enter to show questions)")
	input()
	return time.time()

def ask_questions():
	clear_screen()
	print("Answer all questions below. For multiple answers, separate choices with commas (e.g., A,C):\n")
	# Placeholder for 44 questions
	questions = [
		{
			'q': 'Which of the following are valid Python variable names? (Select all that apply)',
			'choices': ['A) my_var', 'B) 2ndVar', 'C) _var', 'D) var-2'],
			'answer': ['A', 'C'],
			'multi': True
		},
		{
			'q': 'What is the output of print(2 ** 3)?',
			'choices': ['A) 6', 'B) 8', 'C) 9', 'D) 5'],
			'answer': ['B'],
			'multi': False
		},
		# ... Add up to 44 questions here ...
	]
	user_answers = []
	for idx, q in enumerate(questions, 1):
		print(f"Q{idx}: {q['q']}")
		for choice in q['choices']:
			print(f"   {choice}")
		if q['multi']:
			ans = input("Select all that apply (e.g., A,C): ").replace(' ', '').upper().split(',')
		else:
			ans = [input("Select one (A/B/C/D): ").strip().upper()]
		user_answers.append(ans)
		print()
	print("Quiz complete! (Scoring not implemented in this starter)")

def main():
	started = False
	while not started:
		clear_screen()
		print("Welcome to pythonPractice!\n")
		print("[ Get Started ]")
		input("Press Enter to Get Started...")
		started = True
	# After Get Started, disable button (just don't show it again)
	timer_started = False
	while not timer_started:
		print("\n[Get Started (disabled)]  [ Start Timer ]")
		input("Press Enter to Start Timer...")
		timer_started = True
	start_timer()
	ask_questions()

if __name__ == "__main__":
	main()
