echo "Creating etrade_config.py file!"

echo "sender_email = 'your.email@website.com'" > etrade_config.py
echo "password = 'your_password'" >> etrade_config.py
# I have multiple etrade accounts so this is helpful to segregate
echo "ACC_TYPE = { '<ACCOUNT NICKNAME IN ETRADE>': '<ACCOUNT FUNCTION>','stonks': 'Investing'}" >> etrade_config.py
echo "CONSUMER_KEY = 'YOUR CONSUMER KEY'" >> etrade_config.py
echo "CONSUMER_SECRET = 'YOUR CONSUMER SECRET'" >> etrade_config.py
echo "SANDBOX_BASE_URL = 'https://apisb.etrade.com'" >> etrade_config.py
echo "PROD_BASE_URL = 'https://api.etrade.com'" >> etrade_config.py
echo "OPENAIKEY = 'OPENAIKEY' #THIS IS FOR CHAT GPT INTEGRATION" >> etrade_config.py
echo "PERIGON_API_KEY = 'PERIGONKEY' #THIS IS FOR PERIGON SENTIMENT ANALYSIS" >> etrade_config.py
echo "receiver_email = ['your.email@website.com','another.email.if.you.want@gmail.com']" >> etrade_config.py
echo "Setup of etrade config is complete!"
echo "Removing setup etrade config file!"
rm -f setup_etrade_config.sh
