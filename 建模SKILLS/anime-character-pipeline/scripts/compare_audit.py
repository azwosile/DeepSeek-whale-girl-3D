"""对比两份 mesh_audit.py 输出（普通 Python 即可）。
用法: python compare_audit.py 旧.json 新.json
逐对象列出变化的字段；全部一致时打印 IDENTICAL。退出码：0 一致，1 有差异。
"""
import json, sys
a, b = (json.load(open(p, encoding='utf-8'))['objects'] for p in sys.argv[1:3])
diff = 0
for n in sorted(set(a) | set(b)):
    if n not in a or n not in b:
        print(f'[{n}] 只存在于', '新文件' if n in b else '旧文件'); diff += 1; continue
    for k in a[n]:
        if a[n][k] != b[n].get(k):
            print(f'[{n}] {k}: {a[n][k]}  ->  {b[n].get(k)}'); diff += 1
print('IDENTICAL' if diff == 0 else f'{diff} 处差异')
sys.exit(1 if diff else 0)
