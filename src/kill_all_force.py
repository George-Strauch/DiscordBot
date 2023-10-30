import os
"""
Kills any processes that have been orphaned 
"""
if __name__ == '__main__':
    # write the system processes for discord_runner.py to a file
    ps_file = "data/processes.txt"
    os.system(f"ps -ef | grep discord_runner.py > {ps_file}")
    with open(ps_file, 'r') as fp:
        lines = fp.readlines()

    # read those processes in as a string and parse the pids out
    lines = [x.split(" ") for x in lines]
    lines = [[b for b in a if b not in [""]] for a in lines]
    pids = [x[1] for x in lines]
    print(pids)

    # kill those processes
    for pid in pids:
        os.system(f"kill -9 {pid}")

    # clean up
    os.system(f"rm {ps_file}")
