"""
YouTube Shorts 评论爬虫
用法：
    python youtube_shorts_scraper.py <视频ID或Shorts链接>
示例：
    python youtube_shorts_scraper.py sGOTCCVDLtQ
    python youtube_shorts_scraper.py https://www.youtube.com/shorts/sGOTCCVDLtQ
"""
import asyncio
import aiohttp
import csv
import re
import sys
import time

API_KEY = "AIzaSyAYLJtjMyOj47RoNx93oShegeFaM7nrins"
PROXY = "http://127.0.0.1:7892"  # 速云加速器
MAX_CONCURRENT = 200
MAX_RETRIES = 3


def extract_video_id(raw: str) -> str:
    """从 YouTube Shorts URL 中提取视频 ID，或直接当 ID 返回。"""
    patterns = [
        r"youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
        r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",
    ]
    for pat in patterns:
        m = re.search(pat, raw)
        if m:
            return m.group(1)
    if re.fullmatch(r"[a-zA-Z0-9_-]{11}", raw):
        return raw
    print(f"无法识别视频 ID / URL: {raw}")
    sys.exit(1)


async def fetch_replies(session, sem, parent_id, quota_exhausted):
    url = "https://www.googleapis.com/youtube/v3/comments"
    params = {
        "part": "snippet",
        "parentId": parent_id,
        "maxResults": 100,
        "key": API_KEY,
    }
    kwargs = {"params": params}
    if PROXY:
        kwargs["proxy"] = PROXY

    rows = []
    api_errors = 0
    while True:
        if quota_exhausted.is_set():
            break

        data = None
        last_err = None
        for attempt in range(MAX_RETRIES):
            if quota_exhausted.is_set():
                break
            async with sem:
                try:
                    async with session.get(
                        url, timeout=aiohttp.ClientTimeout(total=30), **kwargs,
                    ) as resp:
                        if resp.status == 403:
                            data = await resp.json()
                            if "quota" in str(data).lower():
                                quota_exhausted.set()
                                err = data.get("error", {})
                                print(f"\n[配额耗尽] {err.get('message', err)}")
                            else:
                                print(f"\n[回复 403] parentId={parent_id}")
                            return rows
                        if resp.status >= 500:
                            last_err = f"HTTP {resp.status}"
                            if attempt < MAX_RETRIES - 1:
                                await asyncio.sleep(1.0 * (attempt + 1))
                            continue
                        data = await resp.json()
                    break
                except Exception as e:
                    last_err = e
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(0.3 * (attempt + 1))

        if data is None:
            err_msg = last_err if str(last_err) else type(last_err).__name__
            print(f"\n[回复请求失败] parentId={parent_id} | {err_msg}")
            break

        if "error" in data:
            err = data["error"]
            code = err.get("code")
            if isinstance(code, int) and code >= 500 and api_errors < MAX_RETRIES:
                api_errors += 1
                await asyncio.sleep(1.0 * api_errors)
                continue
            print(f"\n[回复API错误] parentId={parent_id} | code={code}"
                  f" | {err.get('message', '')}")
            break

        api_errors = 0
        for item in data.get("items", []):
            s = item["snippet"]
            rows.append([
                s["authorDisplayName"],
                s["textDisplay"],
                s["likeCount"],
                s["publishedAt"],
            ])

        if "nextPageToken" in data:
            params["pageToken"] = data["nextPageToken"]
        else:
            break
    return rows


async def crawl(video_id: str):
    t0 = time.time()
    safe_name = video_id
    filename = f"shorts_{safe_name}_comments.csv"

    progress = {"count": 0}
    lock = asyncio.Lock()
    sem = asyncio.Semaphore(MAX_CONCURRENT)
    quota_exhausted = asyncio.Event()
    reply_tasks: list[asyncio.Task] = []

    connector = aiohttp.TCPConnector(
        limit=MAX_CONCURRENT,
        limit_per_host=MAX_CONCURRENT,
        ttl_dns_cache=300,
        keepalive_timeout=30,
    )

    async with aiohttp.ClientSession(connector=connector) as session:
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["作者", "内容", "点赞数", "发布时间"])
            f.flush()

            url = "https://www.googleapis.com/youtube/v3/commentThreads"
            params = {
                "part": "snippet,replies",
                "videoId": video_id,
                "maxResults": 100,
                "key": API_KEY,
            }
            main_kwargs = {"params": params}
            if PROXY:
                main_kwargs["proxy"] = PROXY

            page = 0
            api_errors = 0
            while True:
                if quota_exhausted.is_set():
                    break

                page += 1
                data = None
                last_err = None
                for attempt in range(MAX_RETRIES):
                    if quota_exhausted.is_set():
                        break
                    async with sem:
                        try:
                            async with session.get(
                                url, timeout=aiohttp.ClientTimeout(total=30),
                                **main_kwargs,
                            ) as resp:
                                if resp.status == 403:
                                    data = await resp.json()
                                    if "quota" in str(data).lower():
                                        quota_exhausted.set()
                                        err = data.get("error", {})
                                        print(f"\n[配额耗尽] {err.get('message', err)}")
                                    else:
                                        print(f"\n[主评论 403]"
                                              f" {data.get('error', {}).get('message', data)}")
                                    break
                                if resp.status >= 500:
                                    last_err = f"HTTP {resp.status}"
                                    if attempt < MAX_RETRIES - 1:
                                        await asyncio.sleep(1.0 * (attempt + 1))
                                    continue
                                data = await resp.json()
                            break
                        except Exception as e:
                            last_err = e
                            if attempt < MAX_RETRIES - 1:
                                await asyncio.sleep(0.5)

                if quota_exhausted.is_set():
                    break

                if data is None:
                    err_msg = last_err if str(last_err) else type(last_err).__name__
                    print(f"\n主评论请求失败（{MAX_RETRIES}次重试均失败）: {err_msg}")
                    break

                if "error" in data:
                    err = data["error"]
                    code = err.get("code")
                    if isinstance(code, int) and code >= 500 and api_errors < MAX_RETRIES:
                        api_errors += 1
                        await asyncio.sleep(1.0 * api_errors)
                        continue
                    print(f"\n[API错误] code={code} | {err.get('message', err)}")
                    break

                api_errors = 0
                items = data.get("items", [])
                batch = []

                for item in items:
                    top = item["snippet"]["topLevelComment"]
                    s = top["snippet"]
                    comment_id = top["id"]

                    batch.append([
                        s["authorDisplayName"],
                        s["textDisplay"],
                        s["likeCount"],
                        s["publishedAt"],
                    ])

                    already = 0
                    if "replies" in item:
                        for r in item["replies"]["comments"]:
                            rs = r["snippet"]
                            batch.append([
                                rs["authorDisplayName"],
                                rs["textDisplay"],
                                rs["likeCount"],
                                rs["publishedAt"],
                            ])
                            already += 1

                    total = item["snippet"]["totalReplyCount"]
                    if total > already:
                        reply_tasks.append(
                            asyncio.create_task(
                                fetch_replies(session, sem, comment_id, quota_exhausted)
                            )
                        )

                async with lock:
                    writer.writerows(batch)
                    f.flush()
                    progress["count"] += len(batch)

                active = sum(1 for t in reply_tasks if not t.done())
                elapsed = time.time() - t0
                speed = progress["count"] / elapsed if elapsed > 0 else 0
                sys.stdout.write(
                    f"\r  第{page}页 | 已采集 {progress['count']} 条"
                    f" | 回复任务 {active} | {speed:.1f} 条/s | {elapsed:.0f}s"
                )
                sys.stdout.flush()

                if "nextPageToken" in data:
                    params["pageToken"] = data["nextPageToken"]
                else:
                    break

            # 配额耗尽 → 取消所有未完成的回复任务
            if quota_exhausted.is_set():
                cancelled = sum(1 for t in reply_tasks if not t.done())
                for t in reply_tasks:
                    if not t.done():
                        t.cancel()
                print(f"\n  配额耗尽，已取消 {cancelled} 个回复任务")

            pending = sum(1 for t in reply_tasks if not t.done())
            print(f"\n  主评论完毕，等待 {pending} 个回复任务收尾...")

            # 收割回复
            if reply_tasks:
                remaining = len([t for t in reply_tasks if not t.done()])
                for task in asyncio.as_completed(reply_tasks):
                    try:
                        rows = await task
                    except asyncio.CancelledError:
                        remaining -= 1
                        continue
                    if rows:
                        async with lock:
                            writer.writerows(rows)
                            f.flush()
                            progress["count"] += len(rows)
                    remaining -= 1
                    elapsed = time.time() - t0
                    speed = progress["count"] / elapsed if elapsed > 0 else 0
                    sys.stdout.write(
                        f"\r  [收回复] 已采集 {progress['count']} 条"
                        f" | 剩余 {max(remaining, 0)}"
                        f" | {speed:.1f} 条/s | {elapsed:.0f}s"
                    )
                    sys.stdout.flush()

    elapsed = time.time() - t0
    print(f"\n\n完成！共 {progress['count']} 条评论")
    print(f"耗时 {elapsed:.1f} 秒  |  已生成文件：{filename}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    vid = extract_video_id(sys.argv[1])
    print(f"视频 ID: {vid}")
    asyncio.run(crawl(vid))
