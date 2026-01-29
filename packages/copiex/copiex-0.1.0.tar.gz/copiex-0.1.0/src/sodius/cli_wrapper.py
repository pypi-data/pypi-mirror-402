from pathlib import Path
import urllib.request
import zipfile
import subprocess
import json


def init(loc: str, username: str, password: str):
    print("init...")

    base = Path(loc).expanduser().resolve()
    bin_path = base / "copiex.exe"

    config_path = base / "config.json"

    print("reading config...")

    create_config(str(config_path), username, password)


    if bin_path.exists():
        print("sodius initing...")
    else:
        print("sodius sys error.. trying 1 quick fix...")
        install(base)

    print("check passed - starting...")
    start(bin_path)


def start(bin_path: Path):
    subprocess.Popen(
        [str(bin_path)],
        cwd=str(bin_path.parent),
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    print("error: sodius requires more data to run!")


def create_config(path:str, username:str, password:str):

        data = {
        "username": username,
        "password": password,
        }


        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)



def install(install_dir: Path):
    install_dir.mkdir(parents=True, exist_ok=True)

    bin_path = install_dir / "copiex.exe"
    zip_path = install_dir / "copiex.zip"

    if bin_path.exists():
        return

    download(
        "https://copiex.polargix.com/install",
        zip_path
    )

    extract_zip(zip_path, install_dir)

    zip_path.unlink()


def download(url: str, target: Path):
    with urllib.request.urlopen(url) as response, open(target, "wb") as out:
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            out.write(chunk)


def extract_zip(zip_path: Path, target_dir: Path):
    with zipfile.ZipFile(zip_path, "r") as zipf:
        zipf.extractall(target_dir)

def stop():
    print("stop...")
    subprocess.call(
        ["taskkill", "/IM", "copiex.exe", "/F"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )



if __name__ == "__main__":
    #stop()
    init(r"C:\Users\Boldi\PycharmProjects\copiex", "boldi", "teszt1")
