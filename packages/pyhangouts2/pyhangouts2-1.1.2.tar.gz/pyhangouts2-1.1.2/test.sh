# Bash script to test PyHangouts2

# SPDX-FileCopyrightText: 2025 NexusSfan <nexussfan@duck.com>
# SPDX-License-Identifier: GPL-3.0-or-later

. venv.sh

echo "Testing G-ChaTTY, please send some messages to a Space, and also join a Space and talk as a client."
python3 -m pyhangouts2.gchatty
echo "Done."
sleep 1

echo "Testing TheChatWouldBeWatching, please send some messages to a Space."
echo "You will be able to exit with Ctrl+C."
python3 -m pyhangouts2.thechatwouldbewatching
