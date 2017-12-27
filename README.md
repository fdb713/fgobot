# Introduction
Telegram bot for Fate/Grand Order

# Run

install dependencies
```bash
apt install supervisor python3-pip -y
pip3 install -r requirements.txt
```

config the bot
```bash
cat > config.ini << EOF
[fgobot]
token = your_token_without_quotes_here
EOF

cat > /etc/supervisor/conf.d/fgobot.conf << EOF
[program:fgobot]
command=$PWD/main.py
autorestart=true
stdout_logfile=/var/log/supervisor/fgobot.log
redirect_stderr=true
directory=$PWD
EOF
```

start via supervisor
```bash
systemctl restart supervisor
supervisorctl reload

```
# Q&A
please enable privacy settings by `/setprivacy` via [@botfather](tg://resolve?domain=BotFather)
use `/setcommands` to set available commands


for reference only:

```
appmedia - appmedia ranking
drop - drop statistics
hougu - hougu damage quick reference
price - compare JPY to CNY and 3rd-party charge
servant - send link of servants by rare and class from atwiki
summon - summon simulator
wiki - search and send link of servant or other keywords on atwiki page
help - show this message
```
