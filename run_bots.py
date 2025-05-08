import subprocess
import sys
from multiprocessing import Process

def run_script(script_name):
    """Запускает Python-скрипт и логирует ошибки"""
    try:
        subprocess.run([sys.executable, script_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка в {script_name}: {e}")
    except Exception as e:
        print(f"Неизвестная ошибка в {script_name}: {e}")

if __name__ == "__main__":
    scripts = ["cod.py", "bot.py", "script3.py", "script4.py", "script5.py", "script6.py", "script7.py"]  # Добавьте свои файлы
    
    processes = []
    for script in scripts:
        p = Process(target=run_script, args=(script,))
        p.start()
        processes.append(p)
    
    for p in processes:
        p.join()
