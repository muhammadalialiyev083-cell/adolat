"""Run only against an isolated fixture org; this test creates real test records."""

import json
import os
import uuid
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

root = Path(__file__).resolve().parents[2]
artifacts = root / "docs/screenshots/enterprise-v1-1"
artifacts.mkdir(parents=True, exist_ok=True)
base = os.environ.get("BCMS_E2E_URL", "http://127.0.0.1:8001").rstrip("/")
username = os.environ["BCMS_E2E_USERNAME"]
password = os.environ["BCMS_E2E_PASSWORD"]
unique = uuid.uuid4().hex[:8]
errors = []
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        executable_path=os.environ.get("BCMS_CHROMIUM_PATH", "/usr/bin/chromium"),
        args=["--no-sandbox"],
    )
    context = browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
    page = context.new_page()
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(base + "/#/imports")
    expect(page.get_by_role("heading", name="Xush kelibsiz!")).to_be_visible()
    page.screenshot(path=str(artifacts / "login-desktop-light.png"), full_page=True)
    page.get_by_role("button", name="Qorong‘i mavzu", exact=True).click()
    page.screenshot(path=str(artifacts / "login-desktop-dark.png"), full_page=True)
    page.get_by_role("button", name="Yorug‘ mavzu", exact=True).click()
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.get_by_role("button", name="UzHi — Uzluksiz Himoya").last.click()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.screenshot(path=str(artifacts / "login-mobile.png"), full_page=True)
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.get_by_role("button", name="Tizimga kirish", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("kiriting")
    page.get_by_label("Foydalanuvchi nomi", exact=True).fill(username)
    page.get_by_label("Parol", exact=True).fill("Wrong-fixture-password!")
    page.get_by_role("button", name="Parolni ko'rsatish", exact=True).click()
    expect(page.get_by_label("Parol", exact=True)).to_have_attribute("type", "text")
    page.get_by_role("button", name="Parolni yashirish", exact=True).click()
    page.get_by_label("Parol", exact=True).press("Enter")
    expect(page.get_by_role("alert")).to_contain_text("noto")
    expect(page.get_by_label("Parol", exact=True)).to_have_value("")
    page.route(
        "**/api/v1/auth/login",
        lambda route: route.fulfill(status=429, content_type="application/json", body="{}"),
    )
    page.get_by_label("Parol", exact=True).fill(password)
    page.get_by_role("button", name="Tizimga kirish", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("chegarasiga")
    page.unroute("**/api/v1/auth/login")
    page.route(
        "**/api/v1/auth/login",
        lambda route: route.fulfill(
            status=503, content_type="application/json", body='{"detail":"private upstream"}'
        ),
    )
    page.get_by_label("Parol", exact=True).fill(password)
    page.get_by_role("button", name="Tizimga kirish", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("vaqtincha")
    assert "private upstream" not in page.locator("body").inner_text()
    page.unroute("**/api/v1/auth/login")
    page.locator(".login-sso summary").click()
    page.get_by_label("Tashkilot kodi", exact=True).fill("not-configured")
    page.get_by_role("button", name="Kirish usulini tekshirish").click()
    expect(page.get_by_role("status")).to_contain_text("yoqilmagan")
    expect(page.get_by_role("button", name="Korporativ hisob orqali kirish")).to_have_count(0)
    # UI-only fixture for configured discovery; real protocol is tested with RS256 in pytest.
    page.route(
        "**/api/v1/auth/sso/discover",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"enabled":true,"provider":"test-fixture"}',
        ),
    )
    page.get_by_label("Tashkilot kodi", exact=True).fill("test-fixture")
    page.get_by_role("button", name="Kirish usulini tekshirish").click()
    expect(page.get_by_role("button", name="Korporativ hisob orqali kirish")).to_be_visible()
    page.unroute("**/api/v1/auth/sso/discover")
    page.locator(".login-sso summary").click()
    pending = []
    page.route("**/api/v1/auth/login", lambda route: pending.append(route))
    page.get_by_label("Parol", exact=True).fill(password)
    page.evaluate(
        "document.querySelector('.login-card form').requestSubmit(); document.querySelector('.login-card form').requestSubmit();"
    )
    expect(page.get_by_role("button", name="Kirilmoqda…", exact=True)).to_be_disabled()
    expect(page.get_by_label("Parol", exact=True)).to_be_disabled()
    assert len(pending) == 1
    pending[0].continue_()
    page.unroute("**/api/v1/auth/login")
    expect(page.get_by_role("heading", name="Excel / CSV import", exact=True)).to_be_visible()
    # Real four-step CSV workflow with no writes before confirmation.
    name = "SYNTHETIC browser department " + unique
    page.locator("#import-file").set_input_files(
        {
            "name": "fixture.csv",
            "mimeType": "text/csv",
            "buffer": f"key,name,head_name\n{unique},{name},Sinov mas’uli\n".encode(),
        }
    )
    page.get_by_role("button", name="Davom etish", exact=True).click()
    page.get_by_role("button", name="Tekshirish va ko‘rish", exact=True).click()
    expect(page.get_by_text("Yaroqli", exact=True)).to_be_visible()
    assert context.request.get(base + "/api/v1/departments/?search=" + unique).json()["count"] == 0
    page.get_by_role("button", name="Yakuniy ko‘rish").click()
    page.screenshot(path=str(artifacts / "import-confirmation.png"), full_page=True)
    page.get_by_role("checkbox").check()
    page.get_by_role("button", name="Importni tasdiqlash", exact=True).click()
    expect(page.get_by_role("heading", name="Import saqlandi")).to_be_visible()
    assert context.request.get(base + "/api/v1/departments/?search=" + unique).json()["count"] == 1
    # Real evidence questionnaire draft and approval.
    page.goto(base + "/#/bia-questionnaire")
    process = context.request.get(
        base + "/api/v1/processes/?search=SYNTHETIC%20browser%20process"
    ).json()["results"][0]
    page.get_by_label("Biznes jarayoni *", exact=True).select_option(str(process["id"]))
    page.get_by_label("Biznes maqsadi", exact=True).fill("SYNTHETIC interview fixture")
    page.get_by_label("Ish jadvali", exact=True).fill("Test schedule")
    page.get_by_role("button", name="Keyingi", exact=True).click()
    page.get_by_role("button", name="Vaqt oralig‘ini qo‘shish").click()
    for label, value in [
        ("Uzilish davomiyligi (soat)", "2"),
        ("Moliyaviy zarar (UZS)", "100"),
        ("Operatsion ta’sir", "2"),
        ("Huquqiy ta’sir", "1"),
        ("Obro‘ga ta’sir", "2"),
    ]:
        page.get_by_label(label, exact=True).fill(value)
    page.get_by_role("button", name="Keyingi", exact=True).click()
    for label, value in [
        ("RTO (soat) *", "2"),
        ("MTPD (soat) *", "8"),
        ("RPO (daqiqa) *", "30"),
        ("Zaxiralash oralig‘i (daqiqa) *", "60"),
        ("Minimal maqbul xizmat darajasi", "Synthetic minimum"),
        ("Bog‘liqlik farazlari", "Synthetic dependencies"),
        ("Tiklash shartlari", "Synthetic prerequisites"),
        ("Maqsadlarni asoslash", "Fixture interview only"),
    ]:
        page.get_by_label(label, exact=True).fill(value)
    page.get_by_role("button", name="Keyingi", exact=True).click()
    page.get_by_role("button", name="Dalil qo‘shish", exact=True).click()
    for label, value in [
        ("Dalil nomi", "SYNTHETIC interview"),
        ("Manba havolasi yoki hujjat raqami", "SYNTHETIC:test"),
        ("Mas’ul shaxs", "Test owner"),
        ("Yig‘ish sanasi", "2026-01-01"),
        ("Baholash sanasi", "2026-01-02"),
        ("Asos va izoh", "Test fixture only"),
    ]:
        page.get_by_label(label, exact=True).fill(value)
    page.get_by_role("button", name="Keyingi", exact=True).click()
    page.get_by_role("button", name="Qoralamani saqlash", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("saqlandi")
    page.screenshot(path=str(artifacts / "bia-review.png"), full_page=True)
    page.get_by_role("button", name="Tasdiqlash", exact=True).click()
    expect(page.get_by_text("Tasdiqlangan", exact=False).first).to_be_visible()
    # Task creation, progress and management counts from real API records.
    page.goto(base + "/#/management")
    page.get_by_role("button", name="Yangi yozuv", exact=True).click()
    page.locator("#field-title").fill("SYNTHETIC task " + unique)
    users = context.request.get(base + "/api/v1/users/?search=" + username).json()["results"]
    page.locator("#field-assigned_to").select_option(str(users[0]["id"]))
    page.locator("#field-due_date").fill("2026-01-01")
    page.get_by_role("button", name="Saqlash", exact=True).click()
    expect(page.get_by_role("dialog")).to_have_count(0)
    page.get_by_role("row").filter(has_text="SYNTHETIC task " + unique).first.get_by_role(
        "button", name="Bajarilishni yangilash"
    ).click()
    page.get_by_role("button", name="Bajarilmoqda", exact=True).click()
    expect(
        page.get_by_role("row").filter(has_text="SYNTHETIC task " + unique).first
    ).to_contain_text("Bajarilmoqda")
    page.screenshot(path=str(artifacts / "management.png"), full_page=True)
    # Incident creation and response UI.
    page.goto(base + "/#/incidents")
    page.get_by_role("button", name="Yangi yozuv", exact=True).click()
    page.locator("#field-title").fill("SYNTHETIC browser incident " + unique)
    page.locator("#field-owner").select_option(str(users[0]["id"]))
    page.locator("#field-affected_processes").select_option(str(process["id"]))
    page.get_by_role("button", name="Saqlash", exact=True).click()
    expect(page.get_by_role("dialog")).to_have_count(0)
    incident = context.request.get(base + "/api/v1/incidents/?search=" + unique).json()["results"][
        0
    ]
    page.get_by_label("Hodisa", exact=True).select_option(str(incident["id"]))
    page.get_by_label("Biznesga ta’sir", exact=True).fill("Observed fixture interruption")
    page.get_by_role("button", name="Saralangan", exact=True).click()
    expect(page.get_by_label("Hodisa", exact=True)).to_contain_text("Saralangan")
    page.screenshot(path=str(artifacts / "incidents.png"), full_page=True)
    page.goto(base + "/#/integrations")
    expect(page.get_by_text("Monitoring manbasi hali sozlanmagan.")).to_be_visible()
    page.screenshot(path=str(artifacts / "integrations-unconfigured.png"), full_page=True)
    # Expiration clears data and restores the protected page after re-login.
    page.evaluate("window.dispatchEvent(new Event('bcms:session-expired'))")
    expect(page.get_by_role("status")).to_contain_text("Sessiya tugagan")
    page.get_by_label("Foydalanuvchi nomi", exact=True).fill(username)
    page.get_by_label("Parol", exact=True).fill(password)
    page.get_by_label("Parol", exact=True).press("Enter")
    expect(
        page.get_by_role("heading", name="Monitoring integratsiyalari", exact=True).first
    ).to_be_visible()
    page.get_by_role("button", name="Tizimdan chiqish", exact=True).click()
    expect(page.get_by_role("heading", name="Xush kelibsiz!")).to_be_visible()
    assert context.request.get(base + "/api/v1/auth/me").status == 403
    assert not errors, errors
    browser.close()
print(
    json.dumps(
        {
            "status": "passed",
            "workflows": [
                "login",
                "responsive themes",
                "SSO discovery fixtures",
                "duplicate submit",
                "CSV import",
                "evidence BIA",
                "tasks",
                "incidents",
                "integration status",
                "session expiration",
                "logout",
            ],
            "page_errors": errors,
        }
    )
)
