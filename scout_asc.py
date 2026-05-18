from __future__ import annotations

import json
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


OUT_DIR = Path("artifacts/asc_scout")
URLS = [
    "https://asc.iitb.ac.in",
    "https://asc.iitb.ac.in/acadmenu",
    "https://asc.iitb.ac.in/academic/CourseRegistration/Common/newallCourse.jsp",
    "https://asc.iitb.ac.in/academic/timetable/TimeTableReports.jsp",
    "https://asc.iitb.ac.in/academic/timetable/TTcheck.jsp",
]


def make_driver() -> webdriver.Chrome:
    options = Options()
    options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    options.add_argument("--window-size=1440,1000")
    options.add_argument("--disable-notifications")
    return webdriver.Chrome(options=options)


def page_snapshot(driver: webdriver.Chrome) -> dict:
    links = []
    for anchor in driver.find_elements(By.TAG_NAME, "a"):
        text = " ".join(anchor.text.split())
        href = anchor.get_attribute("href")
        if text or href:
            links.append({"text": text, "href": href})

    forms = []
    for form in driver.find_elements(By.TAG_NAME, "form"):
        controls = []
        for control in form.find_elements(By.CSS_SELECTOR, "input, select, textarea, button"):
            controls.append(
                {
                    "tag": control.tag_name,
                    "type": control.get_attribute("type"),
                    "name": control.get_attribute("name"),
                    "id": control.get_attribute("id"),
                    "text": " ".join(control.text.split()),
                }
            )
        forms.append(
            {
                "method": form.get_attribute("method"),
                "action": form.get_attribute("action"),
                "controls": controls,
            }
        )

    body_text = driver.execute_script(
        "return document.body ? document.body.innerText : document.documentElement.innerText || ''"
    )
    return {
        "url": driver.current_url,
        "title": driver.title,
        "body_text_start": body_text[:2000],
        "links": links[:200],
        "forms": forms,
    }


def collect_frames(driver: webdriver.Chrome) -> list[dict]:
    frames = []
    for index, frame in enumerate(driver.find_elements(By.CSS_SELECTOR, "frame, iframe")):
        driver.switch_to.default_content()
        name = frame.get_attribute("name")
        frame_id = frame.get_attribute("id")
        src = frame.get_attribute("src")
        try:
            driver.switch_to.frame(frame)
            snapshot = page_snapshot(driver)
        except Exception as exc:  # noqa: BLE001 - scout script should keep going.
            snapshot = {"error": repr(exc)}
        frames.append({"index": index, "name": name, "id": frame_id, "src": src, "snapshot": snapshot})
    driver.switch_to.default_content()
    return frames


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    driver = make_driver()
    wait = WebDriverWait(driver, 12)
    results = []

    try:
        for index, url in enumerate(URLS, start=1):
            driver.get(url)
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            snapshot = page_snapshot(driver)
            snapshot["frames"] = collect_frames(driver)
            screenshot_path = OUT_DIR / f"{index:02d}.png"
            html_path = OUT_DIR / f"{index:02d}.html"
            driver.save_screenshot(str(screenshot_path))
            html_path.write_text(driver.page_source, encoding="utf-8")
            snapshot["screenshot"] = str(screenshot_path)
            snapshot["html"] = str(html_path)
            results.append(snapshot)
    finally:
        driver.quit()

    (OUT_DIR / "summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
