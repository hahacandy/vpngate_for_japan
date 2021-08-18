import os
import sys
import time
import requests
import re
from bs4 import BeautifulSoup
import random


url = requests.get("https://www.vpngate.net/en")
soup = BeautifulSoup(url.content, "lxml")

vpn_lists = []



def get_vpn_lists():

    for temp in soup.select('#vg_hosts_table_id > tr'):
        temp = str(temp)
        if 'Mbps' in temp and 'Japan' in temp:
            vpn_url = re.search(r'([\w]+|public-vpn-[0-9]+).opengw.net', temp)[0]
            vpn_ip = re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", temp)[0]
            vpn_spped = re.search(r"\d{1,3}\.\d{1,3}\ Mbps", temp)[0]
            
            if '219.100' not in vpn_ip:
                vpn_lists.append({'url':vpn_url, 'ip':vpn_ip, 'speed':vpn_spped})
			
            
def show_vpn_lists():
    for idx, vpn in enumerate(vpn_lists):
        print("vpn번호: " + str(idx+1))
        print(vpn['url'], vpn['ip'], vpn['speed'])
        print()
    
    
def connect_vpn(_user_number):
    choice_vpn = vpn_lists[_user_number-1]
    os.system('cls')
    print("선택한 vpn정보")
    print('url:' + choice_vpn['url'])
    print('ip:' + choice_vpn['ip'])
    print('speed:' + choice_vpn['speed'])
    
    a = open("VPN연결정보.txt", "w")  # VPN 연결정보 작성
    a.write('url : ' + choice_vpn['url'] + "\n")
    a.write('ip : ' + choice_vpn['ip'] + "\n")
    a.write('speed : ' + choice_vpn['speed'] + "\n")
    a.close()
    
    cmd = str("PowerShell Add-VpnConnection 'NewVpn' '" + choice_vpn['url'] + "' -RememberCredential")
    os.system(cmd)
    time.sleep(2)
    print("Add to Complete")
    os.system(str("rasdial NewVpn vpn vpn"))  # VPN 연결 시도
    print("Connect to Complete")
    	
        
os.system("Disconnect.bat")
get_vpn_lists()
show_vpn_lists()
user_number = int(input("선택할 vpn의 번호를 입력: "))
connect_vpn(user_number)