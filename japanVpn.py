import os
import sys
import time
import requests
import re
from bs4 import BeautifulSoup
import shutil



#ファイルの経路、　パソコンによって違うかも知らないので
path_openvpn_gui = "C:\\Program Files\\OpenVPN\\bin\\openvpn-gui.exe"
path_openvpn_config = "C:/Users/desk/OpenVPN/config/"


vpn_lists = []



#vpn gate のサイトからｖｐｎの情報を持ってくる
def get_vpn_lists():

    url = requests.get("https://www.vpngate.net/en")
    soup = BeautifulSoup(url.content, "lxml")
    
    for temp in soup.select('#vg_hosts_table_id > tr'):
        
        temp2 = temp
        temp = str(temp)
        
        if 'Mbps' in temp and 'Japan' in temp:
            try:
                vpn_url = re.search(r'([\w]+|public-vpn-[0-9]+).opengw.net', temp)[0]
                vpn_ip = re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", temp)[0]
                vpn_spped = re.search(r"\d{1,3}\.\d{1,3} Mbps", temp)[0]
                vpn_days = re.search(r"\d{1,3} days", temp)[0]
            
                if '219' != vpn_ip[0:3]: # 219のipは既にブロックされている場合が多い為
                    tags_a = temp2.find_all('a')
                    for tag_a in tags_a:
                        if 'openvpn' in tag_a.get('href'):
                            vpn_href = 'https://www.vpngate.net/en/'+tag_a.get('href')
                            vpn_lists.append({'url':vpn_url, 'ip':vpn_ip, 'speed':vpn_spped, 'days':vpn_days, 'href':vpn_href})
                            break
                    
            except:
                pass
            

            
#持ってきたｖｐｎを表示する
def show_vpn_lists():
    for idx, vpn in enumerate(vpn_lists):
        print("vpn번호: " + str(idx+1))
        print(vpn['url'], ',' , vpn['ip'], ',' , vpn['speed'], ',' , vpn['days'])
        print()
    
    
def connect_vpn(_user_number):
    
    #　もし接続した場合は切る
    a = open("Disconnect.bat", "w")  
    a.write('"C:/Program Files/OpenVPN/bin/openvpn-gui.exe" --command disconnect_all')
    a.close()
    os.system("Disconnect.bat")
    
    
    #　選択したｖｐｎのconfigファイルをダウンロードする
    choice_vpn = vpn_lists[_user_number-1]
    
    url2 = requests.get(choice_vpn['href'])
    soup2 = BeautifulSoup(url2.content, "lxml")
    
    for temp in soup2.select('.listBigArrow'):
        ovpn_url = temp.find('a').get('href')
        if 'openvpn_download' in ovpn_url:
            try:
                shutil.rmtree(path_openvpn_config + 'vpn')
            except:
                pass
            createFolder(path_openvpn_config + 'vpn')
            download('https://www.vpngate.net' + temp.find('a').get('href'), path_openvpn_config + 'vpn/vpn.ovpn')
            break
    
    
    #選択したｖｐｎを情報を表示
    os.system('cls')
    print("선택한 vpn정보")
    print('url:' + choice_vpn['url'])
    print('ip:' + choice_vpn['ip'])
    print('speed:' + choice_vpn['speed'])
    print('days:' + choice_vpn['days'])
    
    a = open("VPN연결정보.txt", "w")  # VPN 연결정보 작성
    a.write('url : ' + choice_vpn['url'] + "\n")
    a.write('ip : ' + choice_vpn['ip'] + "\n")
    a.write('speed : ' + choice_vpn['speed'] + "\n")
    a.write('days : ' + choice_vpn['days'] + "\n")
    a.close()
    
    
    #実際の接続
    a = open("Connect.bat", "w")  
    a.write("\"" + path_openvpn_gui + "\"" + " --connect \"vpn.ovpn\"")
    a.close()
    
    os.system("Connect.bat")
    
    
    
def download(url, file_name):
    with open(file_name, "wb") as file:   # open in binary mode
        response = requests .get(url)               # get request
        file.write(response.content)      # write to file 
    
        
def createFolder(directory):
                try:
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                except OSError:
                    print ('Error: Creating directory. ' +  directory) 
        
        
while(True):
    get_vpn_lists()
    show_vpn_lists()

    user_number = int(input("선택할 vpn의 번호를 입력: "))
    connect_vpn(user_number)