import time
import multiprocessing


def cpu_load():
    while True:
        pass


def generate_load(target_percent):
    num_cores = multiprocessing.cpu_count()
    processes = []
    for _ in range(int(num_cores * target_percent)):
        p = multiprocessing.Process(target=cpu_load)
        p.start()
        processes.append(p)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for p in processes:
            p.terminate()


if __name__ == "__main__":
    generate_load(0.8)  # 0.5 represents 50% CPU usage
