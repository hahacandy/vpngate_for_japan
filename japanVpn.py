import os
import requests
import re
import subprocess
import time
from bs4 import BeautifulSoup
from pathlib import Path

# ==========================================
# 설정 (실제 경로 고정)
# ==========================================
OPENVPN_GUI_PATH = r"C:\Program Files\OpenVPN\bin\openvpn-gui.exe"
CONFIG_DIR = Path(r"C:\Users\ecece\OpenVPN\config\vpn")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 색상 코드
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

vpn_lists = []

def get_my_ip():
    try:
        return requests.get("https://api.ipify.org", timeout=5).text.strip()
    except:
        return "0.0.0.0"

def get_vpn_lists():
    global vpn_lists
    vpn_lists = []
    print("🌐 [가정용 개인 아이피] 서버만 선별하는 중...")
    
    # 일본의 주요 가정용 ISP 키워드 (이 문구가 포함되어야 개인 아이피일 확률이 높음)
    residential_keywords = [
        'bbtec', 'ocn', 'so-net', 'u-netsurf', 'dion', 'nifty', 
        'hi-ho', 'home.ne.jp', 'mesh.ad.jp', 'kopti', 'e-net', 
        'itscom', 'flets', 't-com', 'zoot'
    ]

    try:
        response = requests.get("https://www.vpngate.net/en/", headers=HEADERS, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")
        
        all_rows = soup.find_all('tr')
        for row in all_rows:
            row_text = row.get_text(separator=' ', strip=True).lower()
            link_tag = row.find('a', href=re.compile(r'do_openvpn\.aspx'))
            
            # 1. 일본 서버이면서 OpenVPN이 가능한가?
            if 'japan' in row_text and link_tag:
                try:
                    ip_match = re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", row_text)
                    if not ip_match: continue
                    vpn_ip = ip_match.group()


                    # 3. [핵심] 가정용 ISP 키워드가 포함되어 있는가? (개인 아이피 판별)
                    if not any(k in row_text for k in residential_keywords):
                        continue

                    speed_match = re.search(r"(\d+\.?\d*)\s?mbps", row_text, re.IGNORECASE)
                    vpn_speed = speed_match.group(0) if speed_match else "Unknown"

                    # 호스트네임 추출
                    host_match = re.search(r"[a-zA-Z0-9-]+\.opengw\.net", row_text)
                    vpn_url = host_match.group() if host_match else vpn_ip

                    vpn_href = 'https://www.vpngate.net/en/' + link_tag.get('href')

                    vpn_lists.append({'url': vpn_url, 'ip': vpn_ip, 'speed': vpn_speed, 'href': vpn_href})
                except: continue
        
        # 속도 순 정렬
        vpn_lists.sort(key=lambda x: float(re.search(r"\d+\.?\d*", x['speed']).group()) if 'Unknown' not in x['speed'] else 0, reverse=True)
        print(f"✅ 필터링 성공: {len(vpn_lists)}개의 개인용 서버를 발견했습니다!")
        
    except Exception as e:
        print(f"❌ 접속 오류: {e}")

def connect_vpn(choice_idx):
    subprocess.run([OPENVPN_GUI_PATH, "--command", "disconnect_all"], capture_output=True)
    time.sleep(1)
    
    choice_vpn = vpn_lists[choice_idx]
    print(f"\n📡 [{choice_vpn['ip']}] 최적의 개인 서버로 연결 시도 중...")
    
    try:
        res = requests.get(choice_vpn['href'], headers=HEADERS, timeout=10)
        inner_soup = BeautifulSoup(res.text, "html.parser")
        
        ovpn_link = None
        for a in inner_soup.find_all('a', href=True):
            if '.ovpn' in a['href']:
                ovpn_link = 'https://www.vpngate.net' + a['href']
                if 'udp' in a['href'].lower(): break
        
        if ovpn_link:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            ovpn_path = CONFIG_DIR / "vpn.ovpn"
            ovpn_data = requests.get(ovpn_link, headers=HEADERS).text
            
            # IP 강제 지정
            ovpn_data = re.sub(r'^remote\s+\S+', f'remote {choice_vpn["ip"]}', ovpn_data, flags=re.MULTILINE)

            # 암호화 및 호환성 설정
            compatibility_settings = (
                "\n# Security Compatibility\n"
                "data-ciphers AES-128-CBC:AES-256-GCM:AES-128-GCM:CHACHA20-POLY1305\n"
                "data-ciphers-fallback AES-128-CBC\n"
                "ignore-unknown-option data-ciphers data-ciphers-fallback\n"
            )
            
            with open(ovpn_path, "w", encoding="utf-8") as f:
                f.write(ovpn_data + compatibility_settings)

            subprocess.Popen([OPENVPN_GUI_PATH, "--connect", "vpn.ovpn"])
            print(f"🚀 연결 명령 완료! (IP: {choice_vpn['ip']})")
        else:
            print("❌ 설정 파일 링크를 찾지 못했습니다.")
    except Exception as e:
        print(f"❌ 연결 오류: {e}")

def main():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        my_ip = get_my_ip()
        get_vpn_lists()
        
        if vpn_lists:
            print(f"\n🏠 현재 내 공인 IP: {GREEN}{my_ip}{RESET}")
            print(f"💡 {GREEN}가정용 통신사(Softbank, OCN 등) 아이피만 표시 중입니다.{RESET}")
            print("="*90)
            print(f"{'번호':<4} | {'속도':<15} | {'IP 주소':<15} | {'호스트 주소'}")
            print("-" * 90)
            
            for idx, vpn in enumerate(vpn_lists):
                line = f"[{idx + 1:2}] | {vpn['speed']:<15} | {vpn['ip']:<15} | {vpn['url']}"
                if vpn['ip'] == my_ip:
                    print(f"{RED}{line} <--- 현재 접속 중{RESET}")
                else:
                    print(line)
            print("="*90)
            
            try:
                cmd = input("\n연결 번호 (q:종료, r:새로고침): ").lower().strip()
                if cmd == 'q': break
                if cmd == 'r': continue
                idx = int(cmd) - 1
                if 0 <= idx < len(vpn_lists):
                    connect_vpn(idx)
                    time.sleep(5)
            except: pass
        else:
            print("⚠️ 현재 조건에 맞는 가정용 서버가 없습니다. 잠시 후 새로고침하세요.")
            time.sleep(5)

if __name__ == "__main__":
    main()