import re
from playwright.sync_api import sync_playwright


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        page.goto("https://10.156.2.113")
        page.get_by_role("button", name="高级").click()
        page.get_by_role("link", name="继续前往10.220.85.2（不安全）").click()
        page.locator("#login_user").click()
        page.locator("#login_user").fill("admin")
        page.locator("#login_password").click()
        page.locator("#login_password").press("CapsLock")
        page.locator("#login_password").fill("Q")
        page.locator("#login_password").press("CapsLock")
        page.locator("#login_password").fill("Qwer1234")
        page.get_by_role("checkbox", name="我已认真阅读并同意").check()
        page.get_by_text("登录", exact=True).click()
        page.get_by_text("平台管理").nth(1).click()
        page.locator("div").filter(has_text=re.compile(r"^平台配置$")).click()
        page.get_by_role("menuitem", name="接口管理", exact=True).click()
        page.get_by_text("eth9", exact=True).click()
        page.get_by_role("checkbox", name="启用").uncheck()
        page.get_by_role("button", name="确定").click()
        page.get_by_text("eth9", exact=True).click()
        page.get_by_role("checkbox", name="启用").check()
        page.locator("#ext-comp-2388").get_by_role("cell", name="确定").click()
        
        page.wait_for_timeout(3000)
        browser.close()


if __name__ == "__main__":
    main()