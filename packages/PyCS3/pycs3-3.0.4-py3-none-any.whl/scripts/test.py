from multiprocess import Pool
import os

def test(i):
    print(f"Running task {i} on PID {os.getpid()}")

if __name__ == "__main__":
    with Pool(processes=4) as p:
        p.map(test, range(10))