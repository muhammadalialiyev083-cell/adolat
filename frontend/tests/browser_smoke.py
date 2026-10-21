import json
import os
import uuid
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

root = Path(__file__).resolve().parents[2]
artifacts = root / "work/browser"
artifacts.mkdir(parents=True, exist_ok=True)
base_url = os.environ.get("BCMS_E2E_URL", "http://127.0.0.1:8000").rstrip("/")
department_name = "Brauzer sinovi " + uuid.uuid4().hex[:8]
password = os.environ["BCMS_E2E_PASSWORD"]
errors = []
failures = []
with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=os.environ.get("BCMS_CHROMIUM_PATH", "/usr/bin/chromium"),
        headless=True,
        args=["--no-sandbox"],
    )
    context = browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
    page = context.new_page()
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(base_url + "/")
    page.get_by_label("Foydalanuvchi nomi").fill(os.environ.get("BCMS_E2E_USERNAME", "demo_admin"))
    page.get_by_label("Parol", exact=True).fill("Wrong-password!54")
    page.get_by_role("button", name="Tizimga kirish", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("noto")
    page.get_by_label("Parol", exact=True).fill(password)
    page.get_by_role("button", name="Tizimga kirish", exact=True).click()
    expect(page.get_by_role("heading", name="Boshqaruv paneli", exact=True)).to_be_visible()
    expect(page.get_by_text("O‘quv universiteti · DEMO ma’lumotlar.", exact=False)).to_be_visible()
    page.wait_for_timeout(700)
    page.screenshot(path=str(artifacts / "dashboard-desktop.png"), full_page=True)
    for key, title in [
        ("organizations", "Tashkilot profili"),
        ("departments", "Bo‘limlar"),
        ("users", "Xodimlar va rollar"),
        ("services", "Xizmatlar"),
        ("processes", "Biznes jarayonlari"),
        ("assets", "Aktivlar"),
        ("dependencies", "Bog‘liqlik xaritasi"),
        ("bia", "Biznesga ta’sir (BIA)"),
        ("risks", "Risklar reyestri"),
        ("controls", "Nazorat choralari"),
        ("strategies", "Tiklash strategiyalari"),
        ("resources", "Tiklash resurslari"),
        ("schedule", "Tiklash jadvali"),
        ("plans", "Uzluksizlik rejalari"),
        ("scenarios", "Uzilish ssenariylari"),
        ("simulation-runs", "Simulyatsiya natijalari"),
        ("exercises", "Mashqlar"),
        ("audit-logs", "Audit jurnali"),
        ("password", "Parolni almashtirish"),
        ("wizard", "BCMS loyihalash ustasi"),
    ]:
        page.locator(".nav-item").filter(has_text=title).click()
        expect(page.locator("h1")).to_have_text(title)
        page.wait_for_timeout(300)
        if page.locator('[role="alert"]').count():
            failures.append((key, page.locator('[role="alert"]').all_text_contents()))
    page.goto(base_url + "/#/departments")
    expect(page.get_by_role("heading", name="Bo‘limlar", exact=True).first).to_be_visible()
    page.get_by_role("button", name="Yangi yozuv", exact=True).click()
    page.locator("#field-name").fill(department_name)
    page.locator("#field-head_name").fill("Test mas’uli")
    page.get_by_role("button", name="Saqlash", exact=True).click()
    expect(page.get_by_role("dialog")).to_have_count(0)
    expect(page.get_by_role("cell", name=department_name, exact=True)).to_be_visible()
    page.reload()
    expect(page.get_by_role("cell", name=department_name, exact=True)).to_be_visible()
    page.get_by_role("row").filter(has_text=department_name).get_by_role(
        "button", name="Tahrirlash"
    ).click()
    page.locator("#field-head_name").fill("Yangilangan mas’ul")
    page.get_by_role("button", name="Saqlash", exact=True).click()
    expect(
        page.get_by_role("row")
        .filter(has_text=department_name)
        .get_by_role("cell", name="Yangilangan mas’ul", exact=True)
    ).to_be_visible()
    # Dirty form, keyboard focus and cancel confirmation.
    page.get_by_role("button", name="Yangi yozuv", exact=True).click()
    page.locator("#field-name").fill("Saqlanmagan")
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_role("button", name="Bekor qilish").click()
    expect(page.get_by_role("dialog")).to_be_visible()
    page.once("dialog", lambda dialog: dialog.accept())
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog")).to_have_count(0)
    # API outage produces a readable error and retry button.
    page.route(
        "**/api/v1/assets/**",
        lambda route: route.fulfill(
            status=503, content_type="application/json", body='{"detail":"Sinov uzilishi"}'
        ),
    )
    page.locator(".nav-item").filter(has_text="Aktivlar").click()
    expect(page.get_by_role("alert")).to_contain_text("Sinov uzilishi")
    expect(page.get_by_role("button", name="Qayta urinish")).to_be_visible()
    page.unroute("**/api/v1/assets/**")
    page.get_by_role("button", name="Qayta urinish").click()
    expect(page.get_by_role("alert")).to_have_count(0)
    # Mobile layout and horizontal overflow.
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(base_url + "/#/dashboard")
    expect(page.locator("h1")).to_have_text("Boshqaruv paneli")
    page.wait_for_timeout(700)
    width = page.evaluate(
        "({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})"
    )
    assert width["scroll"] <= width["client"], width
    page.screenshot(path=str(artifacts / "dashboard-mobile.png"), full_page=True)
    page.get_by_role("button", name="Tizimdan chiqish", exact=True).click()
    expect(page.get_by_role("button", name="Tizimga kirish", exact=True)).to_be_visible()
    # Read-only role cannot see write controls.
    page.get_by_label("Foydalanuvchi nomi").fill(os.environ.get("BCMS_E2E_AUDITOR", "demo_auditor"))
    page.get_by_label("Parol", exact=True).fill(password)
    page.get_by_role("button", name="Tizimga kirish", exact=True).click()
    expect(page.locator("h1")).to_have_text("Boshqaruv paneli")
    page.goto(base_url + "/#/assets")
    expect(page.locator("h1")).to_have_text("Aktivlar")
    expect(page.get_by_role("button", name="Yangi yozuv", exact=True)).to_have_count(0)
    context.clear_cookies()
    page.goto(base_url + "/#/processes")
    expect(page.get_by_role("button", name="Tizimga kirish", exact=True)).to_be_visible()
    browser.close()
assert not errors, errors
assert not failures, failures
(artifacts / "ui-results.json").write_text(
    json.dumps(
        {
            "status": "passed",
            "page_errors": errors,
            "page_failures": failures,
            "mobile_width": width,
            "checks": [
                "invalid_login",
                "all_navigation",
                "create_persist_reload",
                "edit",
                "dirty_cancel",
                "keyboard_escape",
                "api_outage_retry",
                "mobile_overflow",
                "logout",
                "auditor_readonly",
            ],
        },
        ensure_ascii=False,
        indent=2,
    )
)
print(
    "Browser smoke passed: navigation, persistence, edit, dirty form, API outage, mobile, logout and auditor role."
)
