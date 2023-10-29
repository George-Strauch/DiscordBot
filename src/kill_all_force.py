import os

if __name__ == '__main__':
    ps_file = "data/processes.txt"
    os.system(f"ps -ef | grep discord_runner.py > {ps_file}")
    with open(ps_file, 'r') as fp:
        lines = fp.readlines()
    print(lines)
    lines = [x.split(" ") for x in lines]
    lines = [[b for b in a if b not in [""]] for a in lines]
    pids = [x[1] for x in lines]
    print(pids)
    for pid in pids:
        os.system(f"kill -9 {pid}")
