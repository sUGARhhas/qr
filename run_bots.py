import subprocess
import sys
from multiprocessing import Process

def run_cod_bot():
    subprocess.run([sys.executable, "cod.py"])

def run_forwarder_bot():
    subprocess.run([sys.executable, "bot.py"])

if __name__ == "__main__":
    p1 = Process(target=run_cod_bot)
    p2 = Process(target=run_forwarder_bot)
    
    p1.start()
    p2.start()
    
    p1.join()
    p2.join()