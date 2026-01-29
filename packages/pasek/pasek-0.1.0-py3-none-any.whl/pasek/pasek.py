from tqdm import tqdm 
import time

def pasek(co, czas, kroki):
    for z in tqdm(range(kroki) , desc=co):
        time.sleep(czas / 100)



