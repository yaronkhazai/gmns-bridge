# gmns-bridge
# Welcome to the gmns-bridge wiki!

gmns-bridge is a small app that get the data saved in glucologweb (https://www.glucologweb.com/) and send it to Nightscout (http://www.nightscout.info/)
the app can run anywhere and should be scheduled to run every few minutes

the zipped file contains everything needed to run on aws Lambda(https://aws.amazon.com/lambda/) and designed not to exceed the aws Free Tier


# installation guides
[Bulgarian](https://github.com/yaronkhazai/gmns-bridge/blob/main/guides/BG-GlucoMen-NightScout-Manual.pdf)


English - TBD


# installation guides to run local version(not from the zip)
*assuming that you have python3 and pip installed

git clone https://github.com/yaronkhazai/gmns-bridge.git
cd gmns-bridge
pip install PyYAML --target=./src/packages
pip install requests --target=./src/packages

update the config file with your login information

python lambda_function.py 
