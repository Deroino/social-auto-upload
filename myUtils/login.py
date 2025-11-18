import asyncio
import sqlite3

from playwright.async_api import async_playwright

from myUtils.auth import check_cookie
from utils.base_social_media import set_init_script
import uuid
from pathlib import Path
from conf import BASE_DIR

# 抖音登录
async def douyin_cookie_gen(id,status_queue):
    url_changed_event = asyncio.Event()
    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()
    async with async_playwright() as playwright:
        options = {
            'headless': False
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://creator.douyin.com/")
        original_url = page.url
        img_locator = page.get_by_role("img", name="二维码")
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        print("✅ 图片地址:", src)
        status_queue.put(src)
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)
        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            status_queue.put("500")
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(3, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()

            # 检查是否已存在该账户
            cursor.execute('SELECT id, filePath FROM user_info WHERE type = ? AND userName = ?', (3, id))
            existing_user = cursor.fetchone()

            if existing_user:
                # 更新现有账户
                old_file_path = existing_user[1]

                # 删除旧的cookie文件
                old_cookie_file = cookies_dir / old_file_path
                if old_cookie_file.exists():
                    old_cookie_file.unlink()
                    print(f"🗑️ 已删除旧cookie文件: {old_file_path}")

                cursor.execute('''
                    UPDATE user_info
                    SET filePath = ?, status = ?
                    WHERE type = ? AND userName = ?
                    ''', (f"{uuid_v1}.json", 1, 3, id))
                print("✅ 用户账户已更新")
            else:
                # 插入新账户
                cursor.execute('''
                    INSERT INTO user_info (type, filePath, userName, status)
                    VALUES (?, ?, ?, ?)
                    ''', (3, f"{uuid_v1}.json", id, 1))
                print("✅ 新用户账户已创建")

            conn.commit()
        status_queue.put("200")


# 视频号登录
async def get_tencent_cookie(id,status_queue):
    url_changed_event = asyncio.Event()
    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()

    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': False,  # Set headless option here
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        # Pause the page, and start recording manually.
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto("https://channels.weixin.qq.com")
        original_url = page.url

        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        # 等待 iframe 出现（最多等 60 秒）
        iframe_locator = page.frame_locator("iframe").first

        # 获取 iframe 中的第一个 img 元素
        img_locator = iframe_locator.get_by_role("img").first

        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        print("✅ 图片地址:", src)
        status_queue.put(src)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(2,f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()

            # 检查是否已存在该账户
            cursor.execute('SELECT id, filePath FROM user_info WHERE type = ? AND userName = ?', (2, id))
            existing_user = cursor.fetchone()

            if existing_user:
                # 更新现有账户
                old_file_path = existing_user[1]

                # 删除旧的cookie文件
                old_cookie_file = cookies_dir / old_file_path
                if old_cookie_file.exists():
                    old_cookie_file.unlink()
                    print(f"🗑️ 已删除旧cookie文件: {old_file_path}")

                cursor.execute('''
                    UPDATE user_info
                    SET filePath = ?, status = ?
                    WHERE type = ? AND userName = ?
                    ''', (f"{uuid_v1}.json", 1, 2, id))
                print("✅ 用户账户已更新")
            else:
                # 插入新账户
                cursor.execute('''
                    INSERT INTO user_info (type, filePath, userName, status)
                    VALUES (?, ?, ?, ?)
                    ''', (2, f"{uuid_v1}.json", id, 1))
                print("✅ 新用户账户已创建")

            conn.commit()
        status_queue.put("200")

# 快手登录
async def get_ks_cookie(id,status_queue):
    url_changed_event = asyncio.Event()
    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()
    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': False,  # Set headless option here
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://cp.kuaishou.com")

        # 定位并点击“立即登录”按钮（类型为 link）
        await page.get_by_role("link", name="立即登录").click()
        await page.get_by_text("扫码登录").click()
        img_locator = page.get_by_role("img", name="qrcode")
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        original_url = page.url
        print("✅ 图片地址:", src)
        status_queue.put(src)
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(4, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()

            # 检查是否已存在该账户
            cursor.execute('SELECT id, filePath FROM user_info WHERE type = ? AND userName = ?', (4, id))
            existing_user = cursor.fetchone()

            if existing_user:
                # 更新现有账户
                old_file_path = existing_user[1]

                # 删除旧的cookie文件
                old_cookie_file = cookies_dir / old_file_path
                if old_cookie_file.exists():
                    old_cookie_file.unlink()
                    print(f"🗑️ 已删除旧cookie文件: {old_file_path}")

                cursor.execute('''
                    UPDATE user_info
                    SET filePath = ?, status = ?
                    WHERE type = ? AND userName = ?
                    ''', (f"{uuid_v1}.json", 1, 4, id))
                print("✅ 用户账户已更新")
            else:
                # 插入新账户
                cursor.execute('''
                    INSERT INTO user_info (type, filePath, userName, status)
                    VALUES (?, ?, ?, ?)
                    ''', (4, f"{uuid_v1}.json", id, 1))
                print("✅ 新用户账户已创建")

            conn.commit()
        status_queue.put("200")

# 小红书登录
async def xiaohongshu_cookie_gen(id,status_queue):
    url_changed_event = asyncio.Event()

    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()

    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': False,  # Set headless option here
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://creator.xiaohongshu.com/")
        await page.locator('img.css-wemwzq').click()

        img_locator = page.get_by_role("img").nth(2)
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        original_url = page.url
        print("✅ 图片地址:", src)
        status_queue.put(src)
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(1, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()

            # 检查是否已存在该账户
            cursor.execute('SELECT id, filePath FROM user_info WHERE type = ? AND userName = ?', (1, id))
            existing_user = cursor.fetchone()

            if existing_user:
                # 更新现有账户
                old_file_path = existing_user[1]

                # 删除旧的cookie文件
                old_cookie_file = cookies_dir / old_file_path
                if old_cookie_file.exists():
                    old_cookie_file.unlink()
                    print(f"🗑️ 已删除旧cookie文件: {old_file_path}")

                cursor.execute('''
                    UPDATE user_info
                    SET filePath = ?, status = ?
                    WHERE type = ? AND userName = ?
                    ''', (f"{uuid_v1}.json", 1, 1, id))
                print("✅ 用户账户已更新")
            else:
                # 插入新账户
                cursor.execute('''
                    INSERT INTO user_info (type, filePath, userName, status)
                    VALUES (?, ?, ?, ?)
                    ''', (1, f"{uuid_v1}.json", id, 1))
                print("✅ 新用户账户已创建")

            conn.commit()
        status_queue.put("200")

# 百家号登录
async def baijiahao_cookie_gen(id, status_queue):
    url_changed_event = asyncio.Event()

    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()

    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': False,
        }
        browser = await playwright.chromium.launch(**options)
        context = await browser.new_context()
        context = await set_init_script(context)
        page = await context.new_page()

        await page.goto("https://baijiahao.baidu.com/builder/theme/bjh/login")
        original_url = page.url

        # 步骤1：点击登录按钮
        await page.get_by_role("button", name="登录/注册百家号").click()

        # 步骤2：等待二维码加载并获取
        await page.wait_for_selector("img.tang-pass-qrcode-img", timeout=10000)
        img_locator = page.locator("img.tang-pass-qrcode-img")
        src = await img_locator.get_attribute("src")

        print("✅ 百家号二维码地址:", src)
        status_queue.put(src)

        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            status_queue.put("500")
            return None

        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(5, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()

            # 检查是否已存在该账户
            cursor.execute('SELECT id, filePath FROM user_info WHERE type = ? AND userName = ?', (5, id))
            existing_user = cursor.fetchone()

            if existing_user:
                # 更新现有账户
                old_file_path = existing_user[1]

                # 删除旧的cookie文件
                old_cookie_file = cookies_dir / old_file_path
                if old_cookie_file.exists():
                    old_cookie_file.unlink()
                    print(f"🗑️ 已删除旧cookie文件: {old_file_path}")

                cursor.execute('''
                    UPDATE user_info
                    SET filePath = ?, status = ?
                    WHERE type = ? AND userName = ?
                    ''', (f"{uuid_v1}.json", 1, 5, id))
                print("✅ 用户账户已更新")
            else:
                # 插入新账户
                cursor.execute('''
                    INSERT INTO user_info (type, filePath, userName, status)
                    VALUES (?, ?, ?, ?)
                    ''', (5, f"{uuid_v1}.json", id, 1))
                print("✅ 新用户账户已创建")

            conn.commit()
        status_queue.put("200")

# TikTok登录
async def tiktok_cookie_gen(id, status_queue):
    url_changed_event = asyncio.Event()

    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()

    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': False,
        }
        browser = await playwright.chromium.launch(**options)
        context = await browser.new_context()
        context = await set_init_script(context)
        page = await context.new_page()

        await page.goto("https://www.tiktok.com/login?lang=en")
        original_url = page.url

        # 步骤1：点击"Use QR code"
        await page.get_by_text("Use QR code").click()

        # 步骤2：等待canvas二维码加载
        await page.wait_for_selector("div[data-e2e='qr-code']", timeout=10000)
        canvas = page.locator("div[data-e2e='qr-code'] canvas")

        # 截取canvas为base64图片
        screenshot_bytes = await canvas.screenshot()
        import base64
        base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
        qr_code_url = f"data:image/png;base64,{base64_image}"

        print("✅ TikTok二维码已生成")
        status_queue.put(qr_code_url)

        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            status_queue.put("500")
            return None

        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(6, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()

            # 检查是否已存在该账户
            cursor.execute('SELECT id, filePath FROM user_info WHERE type = ? AND userName = ?', (6, id))
            existing_user = cursor.fetchone()

            if existing_user:
                # 更新现有账户
                old_file_path = existing_user[1]

                # 删除旧的cookie文件
                old_cookie_file = cookies_dir / old_file_path
                if old_cookie_file.exists():
                    old_cookie_file.unlink()
                    print(f"🗑️ 已删除旧cookie文件: {old_file_path}")

                cursor.execute('''
                    UPDATE user_info
                    SET filePath = ?, status = ?
                    WHERE type = ? AND userName = ?
                    ''', (f"{uuid_v1}.json", 1, 6, id))
                print("✅ 用户账户已更新")
            else:
                # 插入新账户
                cursor.execute('''
                    INSERT INTO user_info (type, filePath, userName, status)
                    VALUES (?, ?, ?, ?)
                    ''', (6, f"{uuid_v1}.json", id, 1))
                print("✅ 新用户账户已创建")

            conn.commit()
        status_queue.put("200")

# a = asyncio.run(xiaohongshu_cookie_gen(4,None))
# print(a)
