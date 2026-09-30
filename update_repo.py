import json
import requests
import re
from urllib.parse import unquote

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
}

ESIGN_REPO = {
    "name": "Benim Otomatik ESign Repom",
    "identifier": "com.benim.esign.repo",
    "sourceURL": "",
    "apps": []
}

def fetch_json_smart(json_url):
    """Cloudflare ve bot korumalarını aşmak için sırayla curl_cffi, cloudscraper ve proxy dener."""
    
    # 1. Yöntem: curl_cffi (Chrome/Safari TLS parmak izini taklit eder - En etkili yöntem)
    try:
        from curl_cffi import requests as cffi_requests
        print(f"Çekiliyor (curl_cffi ile): {json_url}")
        res = cffi_requests.get(json_url, impersonate="chrome120", timeout=20)
        if res.status_code == 200:
            return res.json()
        print(f"curl_cffi başarısız oldu: HTTP {res.status_code}")
    except Exception as e:
        print(f"curl_cffi hatası: {e}")

    # 2. Yöntem: cloudscraper
    try:
        import cloudscraper
        print(f"Çekiliyor (cloudscraper ile): {json_url}")
        scraper = cloudscraper.create_scraper()
        res = scraper.get(json_url, headers=HEADERS, timeout=20)
        if res.status_code == 200:
            return res.json()
        print(f"cloudscraper başarısız oldu: HTTP {res.status_code}")
    except Exception as e:
        print(f"cloudscraper hatası: {e}")

    # 3. Yöntem: Alternatif Proxy'ler
    proxies = [
        f"https://api.allorigins.win/raw?url={json_url}",
        f"https://corsproxy.io/?{json_url}"
    ]
    for p_url in proxies:
        try:
            print(f"Çekiliyor (Proxy ile): {p_url}")
            res = requests.get(p_url, headers=HEADERS, timeout=15)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"Proxy hatası ({p_url}): {e}")

    return None

def get_github_releases(repo_name):
    """GitHub reposundan en son sürümdeki IPA dosyasını çeker."""
    api_url = f"https://api.github.com/repos/{repo_name}/releases/latest"
    try:
        response = requests.get(api_url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            app_name = repo_name.split('/')[-1]
            version = data.get('tag_name', '1.0').replace('v', '')
            
            for asset in data.get('assets', []):
                if asset['name'].endswith('.ipa'):
                    return {
                        "name": app_name,
                        "version": version,
                        "versionDate": data.get('published_at', ''),
                        "versionDescription": data.get('body', 'Otomatik Güncelleme'),
                        "downloadURL": asset['browser_download_url'],
                        "developerName": repo_name.split('/')[0],
                        "size": asset['size'],
                        "iconURL": "https://via.placeholder.com/150"
                    }
    except Exception as e:
        print(f"Hata (GitHub - {repo_name}): {e}")
    return None

def get_telegram_links(channel_name):
    """Telegram Web önizlemesinden IPA linklerini tarar."""
    url = f"https://t.me/s/{channel_name}"
    apps = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        urls = re.findall(r'(https?://[^\s]+?\.ipa)', response.text)
        
        for idx, ipa_url in enumerate(list(set(urls))):
            apps.append({
                "name": f"{channel_name} App {idx+1}",
                "version": "1.0",
                "versionDescription": "Telegram kanalından çekildi",
                "downloadURL": ipa_url,
                "developerName": channel_name,
                "iconURL": "https://via.placeholder.com/150"
            })
    except Exception as e:
        print(f"Hata (Telegram - {channel_name}): {e}")
    return apps

def get_direct_url_app(url):
    """Doğrudan IPA indirme linkini ekler."""
    try:
        file_name = url.split('/')[-1].split('?')[0]
        file_name = unquote(file_name)
        app_name = file_name.replace('.ipa', '').replace('-', ' ').replace('_', ' ').title()
        if not app_name:
            app_name = "Özel Uygulama"

        return {
            "name": app_name,
            "version": "1.0",
            "versionDescription": "Doğrudan URL ile eklendi",
            "downloadURL": url,
            "developerName": "Harici Kaynak",
            "iconURL": "https://via.placeholder.com/150"
        }
    except Exception as e:
        print(f"Hata (Direkt URL - {url}): {e}")
    return None

def get_external_json_apps(json_url):
    """Harici JSON repolarındaki tüm uygulamaları çeker."""
    apps = []
    data = fetch_json_smart(json_url)
    
    if not data:
        print(f"Hata: {json_url} adresinden veri çekilemedi.")
        return apps

    if isinstance(data, dict):
        raw_apps = data.get('apps', [])
    elif isinstance(data, list):
        raw_apps = data
    else:
        raw_apps = []

    for app in raw_apps:
        if not isinstance(app, dict):
            continue

        download_url = app.get('downloadURL') or app.get('downloadUrl') or app.get('download_url') or app.get('url')
        if not download_url:
            continue
        
        icon_url = app.get('iconURL') or app.get('iconUrl') or app.get('icon') or app.get('icon_url') or "https://via.placeholder.com/150"
        
        normalized_app = {
            "name": app.get('name', 'Bilinmeyen Uygulama'),
            "version": str(app.get('version', '1.0')),
            "versionDate": str(app.get('versionDate', app.get('date', ''))),
            "versionDescription": str(app.get('versionDescription', app.get('localizedDescription', app.get('subtitle', 'Harici depodan aktarıldı')))),
            "downloadURL": download_url,
            "developerName": app.get('developerName', app.get('developer', 'Bilinmiyor')),
            "iconURL": icon_url,
            "size": app.get('size', 0)
        }
        apps.append(normalized_app)
        
    print(f"Başarılı: {json_url} adresinden {len(apps)} uygulama çekildi.")
    return apps

def main():
    try:
        with open('sources.json', 'r', encoding='utf-8') as f:
            sources = json.load(f)
    except Exception as e:
        print(f"sources.json okunurken HATA oluştu: {e}")
        return

    # 1. GitHub Repoları
    for repo in sources.get('github_repos', []):
        if repo:
            print(f"İşleniyor: GitHub -> {repo}")
            app_data = get_github_releases(repo)
            if app_data:
                ESIGN_REPO["apps"].append(app_data)
            
    # 2. Telegram Kanalları
    for channel in sources.get('telegram_channels', []):
        if channel:
            print(f"İşleniyor: Telegram -> {channel}")
            telegram_apps = get_telegram_links(channel)
            ESIGN_REPO["apps"].extend(telegram_apps)
        
    # 3. Direkt IPA Linkleri
    for url in sources.get('direct_urls', []):
        if url:
            print(f"İşleniyor: Direkt URL -> {url}")
            app_data = get_direct_url_app(url)
            if app_data:
                ESIGN_REPO["apps"].append(app_data)

    # 4. Harici JSON Repoları (CyPwn vb.)
    for json_url in sources.get('external_json_urls', []):
        if json_url:
            print(f"İşleniyor: Harici JSON -> {json_url}")
            json_apps = get_external_json_apps(json_url)
            ESIGN_REPO["apps"].extend(json_apps)
        
    # Dosyayı Kaydet
    with open('apps.json', 'w', encoding='utf-8') as f:
        json.dump(ESIGN_REPO, f, ensure_ascii=False, indent=4)
        
    print(f"apps.json başarıyla oluşturuldu! Toplam uygulama: {len(ESIGN_REPO['apps'])}")

if __name__ == "__main__":
    main()
