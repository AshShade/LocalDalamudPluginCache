from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import os
import requests
from pathlib import Path
import json


HOST = "localhost"  # Use "0.0.0.0" to make it accessible from other devices
PORT = 8000
CACHE_FOLDER = "plugins"

# Function to download a file
def download_file(url, save_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Write the file in chunks to handle large files
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"    Downloaded: {save_path}")
    except requests.exceptions.RequestException as e:
        print(f"    Failed to download {url}: {e}")

def update_plugins():
    plugin_set = {}
    with open("follow.txt", "r") as file:
        for line in file:
            url = line.strip()
            print("Reading {}".format(url))
            response = requests.get(url)
            response.raise_for_status()
            plugin_list = response.json()
            for plugin in plugin_list:
                name = plugin["Name"]
                if name not in plugin_set:
                    plugin_set[name] = plugin
                    download_link = plugin["DownloadLinkInstall"]
                    version = plugin["AssemblyVersion"]
                    local_file_name = f"{version}.zip"
                    local_path = os.path.join(CACHE_FOLDER, name, local_file_name)
                    if not os.path.exists(local_path):
                        print(f"    Downloading {name} {version} from {download_link}")
                        folder_path = os.path.join(CACHE_FOLDER, name)
                        os.makedirs(folder_path, exist_ok=True)
                        download_file(download_link, local_path)
                    local_url = f"http://{HOST}:{PORT}/{name}/{local_file_name}"
                    plugin["DownloadLinkInstall"] = local_url
                    plugin["DownloadLinkUpdate"] = local_url
                    
        with open("plugins/pluginmaster.json", "w") as file:
            json.dump(list(plugin_set.values()), file,indent=4)
        print()

class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, directory=CACHE_FOLDER)

def start_server():
    with TCPServer((HOST, PORT), CustomHandler) as httpd:
        print(f"Serving HTTP on {HOST}:{PORT}")
        httpd.serve_forever()

if __name__ == '__main__':
    update_plugins()
    start_server()