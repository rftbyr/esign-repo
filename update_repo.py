import json
import requests
import re
from urllib.parse import unquote

# ESign için temel JSON şablonu
ESIGN_REPO = {
    "name": "Benim Otomatik ESign Repom",
    "identifier": "com.benim.esign.repo",
    "sourceURL": "",
    "apps": []
}

def get_github_releases(repo_name):
    """GitHub reposundan en son sürümdeki IPA dosyasını çeker."""
    api_url = f"https://api.github.com/repos/{repo_name}/releases/latest"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
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
        response = requests.get(url, timeout=10)
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
    """CyPwn, Scarlet, AltStore gibi harici JSON repolarındaki tüm uygulamaları çeker."""
    apps = []
    try:
        response = requests.get(json_url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            raw_apps = data.get('apps', [])
            
            for app in raw_apps:
                # Farklı repo formatlarındaki isim karmaşasını standart ESign formatına dönüştürüyoruz
                download_url = app.get('downloadURL') or app.get('downloadUrl') or app.get('download_url')
                if not download_url:
                    continue  # İndirme linki yoksa atla
                
                icon_url = app.get('iconURL') or app.get('iconUrl') or app.get('icon') or "https://via.placeholder.com/150"
                
                normalized_app = {
                    "name": app.get('name', 'Bilinmeyen Uygulama'),
                    "version": str(app.get('version', '1.0')),
                    "versionDate": app.get('versionDate', app.get('date', '')),
                    "versionDescription": app.get('versionDescription', app.get('localizedDescription', 'Harici depodan aktarıldı')),
                    "downloadURL": download_url,
                    "developerName": app.get('developerName', app.get('developer', 'Bilinmiyor')),
                    "iconURL": icon_url,
                    "size": app.get('size', 0)
                }
                apps.append(normalized_app)
            print(f"Başarılı: {json_url} adresinden {len(apps)} uygulama çekildi.")
    except Exception as e:
        print(f"Hata (JSON Kaynağı - {json_url}): {e}")
    return apps

def main():
    with open('sources.json', 'r') as f:
        sources = json.load(f)
    
    # 1. GitHub Repoları
    for repo in sources.get('github_repos', []):
        print(f"İşleniyor: GitHub -> {repo}")
        app_data = get_github_releases(repo)
        if app_data:
            ESIGN_REPO["apps"].append(app_data)
            
    # 2. Telegram Kanalları
    for channel in sources.get('telegram_channels', []):
        print(f"İşleniyor: Telegram -> {channel}")
        telegram_apps = get_telegram_links(channel)
        ESIGN_REPO["apps"].extend(telegram_apps)
        
    # 3. Direkt IPA Linkleri
    for url in sources.get('direct_urls', []):
        print(f"İşleniyor: Direkt URL -> {url}")
        app_data = get_direct_url_app(url)
        if app_data:
            ESIGN_REPO["apps"].append(app_data)

    # 4. Harici JSON Repoları (CyPwn vb.)
    for json_url in sources.get('external_json_urls', []):
        print(f"İşleniyor: Harici JSON -> {json_url}")
        json_apps = get_external_json_apps(json_url)
        ESIGN_REPO["apps"].extend(json_apps)
        
    # Dosyayı Kaydet
    with open('apps.json', 'w', encoding='utf-8') as f:
        json.dump(ESIGN_REPO, f, ensure_ascii=False, indent=4)
        
    print("apps.json başarıyla oluşturuldu!")

if __name__ == "__main__":
    main()
