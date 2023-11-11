LOG_FILE="/opt/bot/data/log.txt"
START_SCRIPT="discord_runner.py"
PID_FILE="/opt/bot/data/pid.txt"
mkdir -p data
source ../venv/bin/activate
nohup python  $START_SCRIPT> $LOG_FILE 2>&1 &
echo $! > $PID_FILE