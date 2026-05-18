from __future__ import annotations

import json
import re
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


OUT_DIR = Path("artifacts/asc_authenticated")
ASC_URL = "https://asc.iitb.ac.in/acadmenu/"
AUTH_FILE = Path.home() / ".config/openvpn/iitb.auth"
KEYWORDS = re.compile(
    r"grade|grading|stat|course|cpi|spi|transcript|result|performance|semester|registration|slot|timetable",
    re.I,
)


def make_driver() -> webdriver.Chrome:
    options = Options()
    options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    options.add_argument("--window-size=1440,1000")
    options.add_argument("--disable-notifications")
    options.add_argument(f"--user-data-dir={Path('.chrome-asc-profile').resolve()}")
    return webdriver.Chrome(options=options)


def frame_text(driver: webdriver.Chrome, frame_name: str) -> str:
    driver.switch_to.default_content()
    driver.switch_to.frame(frame_name)
    return driver.execute_script("return document.body ? document.body.innerText : ''")


def extract_frame(driver: webdriver.Chrome, frame_name: str) -> dict:
    driver.switch_to.default_content()
    driver.switch_to.frame(frame_name)
    links = []
    for anchor in driver.find_elements(By.TAG_NAME, "a"):
        text = " ".join(anchor.text.split())
        href = anchor.get_attribute("href")
        title = anchor.get_attribute("title")
        onclick = anchor.get_attribute("onclick")
        if text or href or title or onclick:
            links.append({"text": text, "title": title, "href": href, "onclick": onclick})
    html = driver.page_source
    text = driver.execute_script("return document.body ? document.body.innerText : ''")
    return {"text": text, "links": links, "html": html}


def is_logged_in(driver: webdriver.Chrome) -> bool:
    try:
        left = frame_text(driver, "leftPage")
    except Exception:
        return False
    negative = "Sign in" in left and "LDAP User ID" in left
    positive = any(token in left.lower() for token in ["logout", "sign out", "student", "my courses", "registration"])
    return positive and not negative


def read_auth() -> tuple[str, str]:
    lines = AUTH_FILE.read_text(encoding="utf-8").splitlines()
    if (
        len(lines) < 2
        or not lines[0]
        or not lines[1]
        or "REPLACE_WITH_LDAP_USERNAME" in lines[0]
        or "REPLACE_WITH_VPN_PASSWORD" in lines[1]
    ):
        raise SystemExit(f"Auth file is missing usable credentials: {AUTH_FILE}")
    return lines[0], lines[1]


def submit_login(driver: webdriver.Chrome, username: str, password: str) -> None:
    driver.switch_to.default_content()
    driver.switch_to.frame("rightPage")
    user_field = driver.find_element(By.NAME, "UserName")
    password_field = driver.find_element(By.NAME, "UserPassword")
    user_field.clear()
    user_field.send_keys(username)
    password_field.clear()
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    username, password = read_auth()
    driver = make_driver()
    wait = WebDriverWait(driver, 20)
    driver.get(ASC_URL)
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

    print(f"Opened ASC. Logging in as {username!r} using local auth file.")
    submit_login(driver, username, password)
    print("Waiting up to 2 minutes for the menu to change after login...")

    deadline = time.time() + 120
    while time.time() < deadline:
        if is_logged_in(driver):
            break
        time.sleep(2)
    else:
        driver.save_screenshot(str(OUT_DIR / "timeout.png"))
        raise SystemExit("Timed out waiting for login. Screenshot saved to artifacts/asc_authenticated/timeout.png")

    time.sleep(3)
    driver.save_screenshot(str(OUT_DIR / "after_login.png"))

    frames = {}
    for frame_name in ["leftPage", "rightPage1", "rightPage"]:
        try:
            frames[frame_name] = extract_frame(driver, frame_name)
            (OUT_DIR / f"{frame_name}.html").write_text(frames[frame_name]["html"], encoding="utf-8")
        except Exception as exc:  # noqa: BLE001 - keep scouting.
            frames[frame_name] = {"error": repr(exc)}

    menu_links = frames.get("leftPage", {}).get("links", [])
    matching_links = [
        link
        for link in menu_links
        if KEYWORDS.search(" ".join(str(link.get(k) or "") for k in ["text", "title", "href", "onclick"]))
    ]

    result = {
        "current_url": driver.current_url,
        "title": driver.title,
        "matching_menu_links": matching_links,
        "frame_text": {name: data.get("text", "")[:4000] for name, data in frames.items()},
        "menu_link_count": len(menu_links),
    }
    (OUT_DIR / "authenticated_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print("Browser left open for inspection. Press Ctrl+C in terminal when done.")
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        driver.quit()


if __name__ == "__main__":
    main()
