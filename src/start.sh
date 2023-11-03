LOG_FILE="data/log.txt"
START_SCRIPT="discord_runner.py"
PID_FILE="data/pid.txt"
mkdir -p data
source ../venv/bin/activate
nohup python  $START_SCRIPT> $LOG_FILE 2>&1 &
echo $! > $PID_FILE