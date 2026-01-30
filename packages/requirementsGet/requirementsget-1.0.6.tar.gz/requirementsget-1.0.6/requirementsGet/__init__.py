import ast
import sys
import sysconfig
from pathlib import Path
from importlib.metadata import version, packages_distributions, PackageNotFoundError

# 手动映射一些自动检测可能失败的特殊库
MANUAL_MAPPING = {
    "PIL": "pillow",
    "cv2": "opencv-python",
    "bs4": "beautifulsoup4",
    "sklearn": "scikit-learn",
    "yaml": "pyyaml",
    "Crypto": "pycryptodome",
    "paho": "paho-mqtt",  # 注意通常是短横线
    "mysqldb": "mysqlclient"
}


def get_imports_from_file(file_path):
    """
    使用 AST (抽象语法树) 解析 Python 文件中的 import 语句。
    比正则或字符串处理更准确、安全。
    """
    imports = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # 获取顶层包名 (例如 from os.path import ... -> os)
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # 处理相对导入 (from . import x) -> node.module 为 None
                    imports.add(node.module.split('.')[0])
    except Exception as e:
        print(f"Warning: Failed to parse {file_path}: {e}")
    return imports


def is_std_lib(module_name):
    """
    判断是否为 Python 标准库。
    """
    # 检查内建模块
    if module_name in sys.builtin_module_names:
        return True

    # 检查标准库路径
    try:
        spec = sys.modules.get(module_name)
        if not spec:
            # 尝试查找模块说明
            import importlib.util
            spec = importlib.util.find_spec(module_name)

        if spec and spec.origin:
            # 如果路径在 Python 安装目录的 lib 下，且不在 site-packages 下
            lib_path = sysconfig.get_paths()["stdlib"]
            if lib_path in spec.origin and "site-packages" not in spec.origin:
                return True
    except:
        pass

    return False


def get_installed_distribution(module_name):
    """
    获取模块对应的安装包名称。
    例如: yaml -> PyYAML, cv2 -> opencv-python
    """
    # 1. 优先检查手动映射
    if module_name in MANUAL_MAPPING:
        return MANUAL_MAPPING[module_name]

    # 2. 使用 importlib.metadata 自动查找映射
    # packages_distributions() 返回 {module_name: [dist_name1, ...]}
    dist_map = packages_distributions()
    dists = dist_map.get(module_name)

    if dists:
        # 通常取第一个，但也可能存在冲突
        return dists[0]

    # 如果找不到映射，通常包名就是模块名
    return module_name


def get(
        base_path="./",
        ignore_list=None,
        output_file="requirements.txt"
):
    if ignore_list is None:
        ignore_list = []

    base_path = Path(base_path).resolve()
    current_script_name = Path(__file__).name  # 获取当前脚本名以排除

    all_imports = set()

    # 1. 遍历文件收集 imports
    print(f"Scanning directory: {base_path} ...")
    for file_path in base_path.rglob("*.py"):
        if file_path.name == current_script_name:
            continue
        # 排除虚拟环境目录 (常见目录名)
        if any(part in ['venv', '.venv', 'env', '.idea', '.git', '__pycache__'] for part in file_path.parts):
            continue

        file_imports = get_imports_from_file(file_path)
        all_imports.update(file_imports)

    print(f"Found imports: {all_imports}")

    requirements = set()

    # 2. 过滤和获取版本
    for module in all_imports:
        if module in ignore_list:
            continue

        # 排除本地模块 (当前目录下存在的 .py 文件或包目录)
        if (base_path / (module + ".py")).exists() or (base_path / module).is_dir():
            continue

        # 排除标准库
        if is_std_lib(module):
            continue

        # 获取真实的 PyPI 包名
        package_name = get_installed_distribution(module)

        try:
            # 获取已安装版本
            pkg_version = version(package_name)
            requirements.add(f"{package_name}=={pkg_version}")
        except PackageNotFoundError:
            # 可能是未安装的包，或者只是一个本地文件夹但没被识别
            print(f"Warning: Package '{package_name}' (module: {module}) not installed or not found.")
            # 也可以选择写入不带版本的包名
            # requirements.add(package_name)

    # 3. 写入文件
    output_path = base_path / output_file
    with open(output_path, "w", encoding="utf-8") as f:
        for req in sorted(requirements):
            f.write(req + "\n")

    print(f"Successfully generated {output_path} with {len(requirements)} packages.")

