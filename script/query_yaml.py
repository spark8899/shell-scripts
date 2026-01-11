# pip3 install pyyaml
import yaml

def read_yaml(filename):
    with open(filename, 'r') as file:
        return yaml.safe_load(file)

def write_yaml(filename, data):
    with open(filename, 'w') as file:
        yaml.dump(data, file, default_flow_style=False)

def get_value(filename, key):
    data = read_yaml(filename)
    return data.get(key)

def set_value(filename, key, value):
    data = read_yaml(filename)
    data[key] = value
    write_yaml(filename, data)

# 示例用法
filename = 'config.yaml'

# 创建示例YAML文件
initial_data = {
    'host': 'localhost',
    'port': 5432,
    'debug': True,
    'log_level': 'INFO'
}
write_yaml(filename, initial_data)

# 读取特定键值
print("Host:", get_value(filename, 'host'))
print("Debug mode:", get_value(filename, 'debug'))

# 修改特定键值
set_value(filename, 'port', 5433)
set_value(filename, 'log_level', 'DEBUG')

# 验证修改
print("\n修改后:")
print("Port:", get_value(filename, 'port'))
print("Log level:", get_value(filename, 'log_level'))
