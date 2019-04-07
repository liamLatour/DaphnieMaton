import io
import re

f = io.open("C:\\Users\\Administrateur\\Desktop\\DaphnieMaton\\Code\\kv\\main.kv", "r", encoding='utf8')
if f.mode == 'r':
    contents = f.read()
    result = list(set(re.findall(r"_\(\'(.*?)\'\)", contents)))

    for r in result:
        print('msgid "'+r+'"\nmsgstr ""\n')