from colorama import Fore, Style
import time
import sys

def banner():
    # 1. Animasi Loading ala Hacker
    print(Fore.CYAN + "Connecting to Ryans Cloud...", end="", flush=True)
    for _ in range(3):
        time.sleep(0.5)  # Jeda 0.5 detik per titik
        print(".", end="", flush=True)
    print("\n") # Pindah baris setelah loading selesai
    
    # 2. Banner Utama (ASCII Art RYANS)
    print(f"""{Fore.CYAN}
 ____ __   __    _    _   _ ____  
|  _ \\ \\ / /   / \\  | \\ | / ___| 
| |_) |\\ V /   / _ \\ |  \\| \\___ \\ 
|  _ <  | |   / ___ \\| |\\  |___) |
|_| \\_\\ |_|  /_/   \\_\\_| \\_|____/ 

Telegram : Ryans891
Big Money Never Comes Clean !!!
{Style.RESET_ALL}""")
