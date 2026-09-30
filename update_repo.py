import json
import requests
import re
from datetime import datetime

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
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            app_name = repo_name.split('/')[-1]
            version = data.get('tag_name', '1.0').replace('v', '')
            
            # IPA dosyasını bul
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
                        "iconURL": "https://via.placeholder.com/150" # İsteğe bağlı ikon
                    }
    except Exception as e:
        print(f"Hata ({repo_name}): {e}")
    return None

def get_telegram_links(channel_name):
    """Telegram Web önizlemesinden IPA veya Github linklerini tarar."""
    url = f"https://t.me/s/{channel_name}"
    apps = []
    try:
        response = requests.get(url)
        # Sadece basit bir örnek: Kanaldaki github.com ... .ipa uzantılı linkleri yakalamaya çalışır
        # (Eğer kanal doğrudan dosya yüklüyorsa ek Telegram Bot API entegrasyonu gerekir)
        urls = re.findall(r'(https?://[^\s]+?\.ipa)', response.text)
        
        for idx, ipa_url in enumerate(list(set(urls))): # Benzersiz olanları al
            apps.append({
                "name": f"{channel_name} App {idx+1}",
                "version": "1.0",
                "versionDescription": "Telegram kanalından çekildi",
                "downloadURL": ipa_url,
                "developerName": channel_name,
                "iconURL": "https://via.placeholder.com/150"
            })
    except Exception as e:
        print(f"Hata ({channel_name}): {e}")
    return apps

def main():
    # Kaynakları oku
    with open('sources.json', 'r') as f:
        sources = json.load(f)
    
    # GitHub Repolarını İşle
    for repo in sources.get('github_repos', []):
        print(f"İşleniyor: GitHub -> {repo}")
        app_data = get_github_releases(repo)
        if app_data:
            ESIGN_REPO["apps"].append(app_data)
            
    # Telegram Kanallarını İşle
    for channel in sources.get('telegram_channels', []):
        print(f"İşleniyor: Telegram -> {channel}")
        telegram_apps = get_telegram_links(channel)
        ESIGN_REPO["apps"].extend(telegram_apps)
        
    # Sonuçları apps.json dosyasına yaz
    with open('apps.json', 'w', encoding='utf-8') as f:
        json.dump(ESIGN_REPO, f, ensure_ascii=False, indent=4)
        
    print("apps.json başarıyla oluşturuldu!")

if __name__ == "__main__":
    main()
