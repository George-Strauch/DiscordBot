PID_FILE="data/pid.txt"
pid=`cat $PID_FILE`
kill -9 $pid
