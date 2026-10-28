"""Set English using the real profile screen on a persistent evaluation browser."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'experiments/results/translation_en'
OUT.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch_persistent_context(
        str(ROOT/'.cache/translation-eval-browser'), headless=True,
        executable_path='C:/Users/ISPL/AppData/Local/ms-playwright/chromium-1223/chrome-win64/chrome.exe',
        viewport={'width':1280,'height':900})
    page=browser.pages[0]
    failures=[]
    page.on('pageerror',lambda e: failures.append(str(e)))
    page.goto('http://127.0.0.1:5173/',wait_until='networkidle')
    page.locator('.splash-screen').wait_for(state='detached',timeout=15000)
    page.locator('.screen.active .bnav-item').nth(4).click()
    profile=page.locator('#s-profile')
    profile.wait_for(state='visible')
    profile.locator('.setting-row').nth(3).click()
    page.locator('#s-profile .channel-modal-btn').filter(has_text='English').click()
    page.wait_for_timeout(1000)
    state=page.evaluate('''() => ({locale:localStorage.getItem('uniguide.locale'),profile:JSON.parse(localStorage.getItem('userProfile')),clientId:localStorage.getItem('yhs_client_id'),activeScreen:document.querySelector('.screen.active').id})''')
    assert state['locale']=='en',state
    assert state['profile']['languages']==['en'],state
    page.screenshot(path=str(OUT/'profile-english.png'),full_page=True)
    page.reload(wait_until='networkidle')
    assert page.evaluate("localStorage.getItem('uniguide.locale')")=='en'
    state['persisted_after_reload']=True
    state['page_errors']=failures
    state['browser_scope']='isolated persistent evaluation browser; user normal browser unchanged'
    (OUT/'profile-check.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    browser.close()
    print(json.dumps(state,ensure_ascii=False,indent=2))
