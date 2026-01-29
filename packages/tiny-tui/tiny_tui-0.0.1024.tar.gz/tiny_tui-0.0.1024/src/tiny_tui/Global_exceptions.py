import traceback


def global_exception_handler(exc_type, exc, tb):
	print("\nПроизошла необработанная ошибка:\n")
	traceback.print_exception(exc_type, exc, tb)
	
	try:
		input("\nПрограмма закроется!\nНажмите Enter для выхода...")
	except EOFError:
		pass
	
	return
