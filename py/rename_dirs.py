#!/usr/bin/env python3
"""目录合并 + 重编号：统一为 3位编号-歌名 格式"""
import os, shutil

WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(WORK_DIR, 'static')

# 合并：(旧目录1前缀, 旧目录2前缀, 新目录名)
MERGES = [
    ('4401', '4402', '029-人心不单向 & 半勺糖'),
    ('4501', '4502', '030-半块馒头 & 陪谁走夜路'),
    ('4601', '4602', '031-一张素脸 & 小算盘'),
    ('4701', '4702', '032-由它去 & 只是错觉'),
    ('4801', '4802', '033-多待一会儿 & 忘了在看'),
    ('4901', '4902', '034-山脚起家 & 摔得起'),
    ('5001', '5002', '035-好好吃饭 & 别等'),
    ('5101', '5102', '036-伞该收了 & 那把旧吉他'),
    ('5501', '5502', '040-一针一线 & 仪式感'),
]

# 单目录：(旧前缀, 新编号)
SINGLES = [
    ('17','002'), ('18','003'), ('19','004'), ('20','005'),
    ('21','006'), ('22','007'), ('23','008'), ('24','009'),
    ('25','010'), ('26','011'), ('27','012'), ('28','013'),
    ('29','014'), ('30','015'), ('31','016'), ('32','017'),
    ('33','018'), ('34','019'), ('35','020'), ('36','021'),
    ('37','022'), ('38','023'), ('39','024'), ('40','025'),
    ('41','026'), ('42','027'), ('43','028'),
    ('5200','037'), ('5300','038'), ('5400','039'),
    ('5600','041'), ('5700','042'), ('5800','043'),
    ('5900','044'), ('6000','045'), ('6100','046'),
    ('6200','047'), ('6300','048'), ('6400','049'),
    ('6500','050'), ('6600','051'), ('6700','052'),
    ('6800','053'), ('6900','054'), ('7000','055'),
    ('7100','056'), ('7200','057'),
]

def find_dir(prefix):
    for d in os.listdir(STATIC_DIR):
        if d.startswith(prefix + '-') and os.path.isdir(os.path.join(STATIC_DIR, d)):
            return os.path.join(STATIC_DIR, d)
    return None

def main():
    print("=== 合并拆分目录 ===")
    for p1, p2, new_name in MERGES:
        d1, d2 = find_dir(p1), find_dir(p2)
        if not d1 or not d2:
            print(f"  SKIP: {p1} or {p2} not found"); continue
        new_path = os.path.join(STATIC_DIR, new_name)
        os.makedirs(new_path, exist_ok=True)
        for src in [d1, d2]:
            for f in os.listdir(src):
                shutil.move(os.path.join(src, f), os.path.join(new_path, f))
            os.rmdir(src)
        print(f"  {p1}+{p2} -> {new_name}")

    print("\n=== 重编单目录 ===")
    for prefix, new_num in SINGLES:
        old = find_dir(prefix)
        if not old:
            print(f"  SKIP: {prefix} not found"); continue
        song = os.path.basename(old).split('-', 1)[1]
        new = f"{new_num}-{song}"
        os.rename(old, os.path.join(STATIC_DIR, new))
        print(f"  {prefix}-{song} -> {new}")

    print("\n=== 验证 ===")
    dirs = sorted([d for d in os.listdir(STATIC_DIR)
                   if os.path.isdir(os.path.join(STATIC_DIR, d)) and d[0].isdigit()])
    for d in dirs:
        print(f"  {d}")
    print(f"共 {len(dirs)} 个目录")

if __name__ == '__main__':
    main()
