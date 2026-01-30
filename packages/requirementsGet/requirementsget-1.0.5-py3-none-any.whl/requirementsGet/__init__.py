import inspect
import os
import sys
import sysconfig
from importlib import import_module


def traverse_files(directory):
    for file_name in os.listdir(directory):
        file_path = os.path.join(directory, file_name)
        if os.path.isdir(file_path):
            for i in traverse_files(file_path):
                yield i
        else:
            # 在这里可以对文件进行操作
            if file_path.endswith(".py"):
                yield file_path


LEVE_TOP_FORMAT = {
    "PIL": "pillow",
    "cv2": "opencv-python",
    "bs4": "beautifulsoup4",
    "sqlalchemy": "SQLAlchemy",
    "yaml": "pyyaml",
    "Crypto": "pycryptodome",
    "paho": "paho_mqtt"
}


def init_top_leves():
    directory = sysconfig.get_paths()["purelib"]
    for file_name in os.listdir(directory):
        file_path = os.path.join(directory, file_name)
        if (
                os.path.isdir(file_path)
                and "dist-info" in file_path
                and os.path.exists(file_path + "/top_level.txt")
        ):
            top_levels = (
                open(file_path + "/top_level.txt", "r", encoding="utf-8")
                .read()
                .split("\n")
            )
            package_name = file_path.replace("\\", "/").split("/")
            package_name = package_name[package_name.__len__() - 1].split("-")[0]
            for top_level in top_levels:
                if not top_level:
                    continue
                LEVE_TOP_FORMAT[top_level] = package_name


init_top_leves()


def get_import(f):
    imports = []
    for line in f.split("\n"):
        if "".join(list(line)[0:5]) == "from " and "import " in line:
            line = (
                line.replace("from", "")
                .split("import")[0]
                .replace(" ", "")
                .split(".")[0]
            )
            imports.append(line)
        elif "".join(list(line)[0:7]) == "import ":
            line = line.replace("import", "")
            for item in line.split(","):
                item = item.split(" as ")[0].replace(" ", "").split(".")[0]
                imports.append(item)
    return list(set(imports))


def get(
        BASE_PATH="./",
        IGNORE_LIST=[],
):
    self = sys._getframe(1).f_code.co_filename.split("\\")
    self = self[self.__len__() - 1]
    self = self.split("/")
    self = self[self.__len__() - 1]
    lib_path = sysconfig.get_paths()["purelib"]
    global_imports = []
    for i in traverse_files(BASE_PATH):
        if self in i:
            continue
        with open(i, "r", encoding="utf-8") as f:
            global_imports += get_import(f.read())
            global_imports = list(set(global_imports))
    with open(BASE_PATH + "requirements.txt", "a+", encoding="utf-8") as requirements:
        requirements.truncate(0)
        writed = []
        for item in global_imports:
            if item in IGNORE_LIST:
                continue
            if os.path.exists(BASE_PATH + item):
                continue
            if os.path.exists(BASE_PATH + item + ".py"):
                continue
            if not os.path.exists(lib_path + "/" + item) and not os.path.exists(
                    lib_path + "/" + item + ".py"
            ):
                continue

            version = None
            try:
                version = inspect.getmodule(import_module(item)).__version__
            except:
                pass

            top_level = LEVE_TOP_FORMAT.get(item)
            if top_level:
                item = top_level

            if item in writed:
                continue

            if version:
                item = f"{item}=={version}"
            writed.append(item)
            requirements.write(item + "\n")
