# -*- coding: utf-8 -*-
"""清空 Redis 数据库 — 仅手动执行生效"""
import os
import sys

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from utils.redis_utils import get_redis_client, close_all


def clear_redis():
    """清空当前 Redis DB 中的所有数据"""
    host = Config.REDIS_HOST
    port = Config.REDIS_PORT
    db = Config.REDIS_DB

    print(f"即将清空 Redis: {host}:{port}  DB={db}")
    print("=" * 50)

    client = get_redis_client(decode_responses=True)

    if client is None:
        print("无法连接 Redis，操作终止。")
        return

    # 列出所有 key
    keys = client.keys("*")
    if not keys:
        print("Redis 中没有数据，无需清空。")
    else:
        print(f"找到 {len(keys)} 个 key:")
        for k in keys:
            ttl = client.ttl(k)
            ttl_str = f"TTL={ttl}s" if ttl > 0 else "永不过期"
            print(f"  - {k}  ({ttl_str})")

        # 二次确认
        confirm = input(f"\n确认删除以上 {len(keys)} 个 key？(输入 yes 确认): ")
        if confirm.strip().lower() == "yes":
            client.flushdb()
            print(f"已清空 Redis DB={db}")
        else:
            print("已取消。")

    close_all()


if __name__ == "__main__":
    clear_redis()
