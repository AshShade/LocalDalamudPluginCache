from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import os
import requests
from pathlib import Path
import json
from autodict import AutoDict
from packaging.version import Version

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
        print(f"Downloaded: {save_path.replace(os.sep, '/')}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")

def prepare_folder(folder_path):
    os.makedirs(folder_path, exist_ok=True)
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path): 
            os.remove(file_path)

def update_plugins():
    plugins = AutoDict()
    with open("follow.txt", "r") as file:
        for line in file:
            if line[0] == "#":
                continue
            url = line.strip()
            print("Reading {}".format(url))
            response = requests.get(url)
            response.raise_for_status()
            plugin_list = response.json()
            for plugin in plugin_list:
                name = plugin["Name"]
                api_level = int(plugin["DalamudApiLevel"])
                version = plugin["AssemblyVersion"]
                if not plugins[name][api_level][version]:
                    plugins[name][api_level][version] = plugin
    
    plugins_to_use = []
    for name, apis in plugins.items():
        for api_level, versions in apis.items():
            lastest_version = sorted(versions.keys(), key=Version)[-1]
            plugin = versions[lastest_version]
            download_link = plugin["DownloadLinkInstall"]
            local_file_name = f"{lastest_version}.zip"
            folder_name = f"{name}/API{api_level}"
            local_path = os.path.join(CACHE_FOLDER, folder_name, local_file_name)
            if not os.path.exists(local_path):
                print(f"Downloading {name} {lastest_version} from {download_link}")
                folder_path = os.path.join(CACHE_FOLDER, folder_name)
                prepare_folder(folder_path)
                download_file(download_link, local_path)
            local_url = f"http://{HOST}:{PORT}/{folder_name}/{local_file_name}"
            plugin["DownloadLinkInstall"] = local_url
            plugin["DownloadLinkUpdate"] = local_url
            plugins_to_use.append(plugin)
                    
    with open("plugins/pluginmaster.json", "w") as file:
        json.dump(plugins_to_use, file,indent=4)
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