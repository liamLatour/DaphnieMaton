import io
import re

files = ["C:\\Users\\Administrateur\\Desktop\\DaphnieMaton\\Code\\app\\main.kv", "C:\\Users\\Administrateur\\Desktop\\DaphnieMaton\\Code\\app\\ParametrageV2.py"]

result = ""

for fil in files:
    f = io.open(fil, "r", encoding='utf8')
    if f.mode == 'r':
        result += f.read()

result = list(set(re.findall(r"_\(\'(.*?)\'\)", result)))

for r in result:
    print('msgid "'+r+'"\nmsgstr ""\n')