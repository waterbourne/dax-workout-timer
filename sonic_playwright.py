#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    # Connect to the existing browser
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:18800")
    
    # Get the page
    context = browser.contexts[0] if browser.contexts else browser.new_context()
    pages = context.pages
    
    print(f"Found {len(pages)} pages")
    for i, page in enumerate(pages):
        print(f"Page {i}: {page.title()} - {page.url}")
    
    # Find the Sonic page
    sonic_page = None
    for page in pages:
        if "sonic" in page.url:
            sonic_page = page
            break
    
    if not sonic_page and pages:
        sonic_page = pages[0]
    
    if sonic_page:
        print(f"\nUsing page: {sonic_page.title()}")
        
        # Find all inputs
        inputs = sonic_page.query_selector_all("input")
        print(f"\nFound {len(inputs)} inputs:")
        for i, inp in enumerate(inputs):
            input_type = inp.get_attribute("type") or "text"
            input_name = inp.get_attribute("name") or ""
            input_id = inp.get_attribute("id") or ""
            print(f"  {i}: type={input_type}, name={input_name}, id={input_id}")
        
        # Fill in username and password
        username = "adityabhavnani@gmail.com"
        password = "_8tVqzEaAVSvz2X"
        
        # Try to find and fill username
        for inp in inputs:
            input_type = inp.get_attribute("type") or ""
            input_name = inp.get_attribute("name") or ""
            if input_type == "text" or "user" in input_name.lower():
                print(f"\nFilling username in: type={input_type}, name={input_name}")
                inp.fill(username)
                break
        
        # Try to find and fill password
        for inp in inputs:
            input_type = inp.get_attribute("type") or ""
            input_name = inp.get_attribute("name") or ""
            if input_type == "password":
                print(f"\nFilling password in: type={input_type}, name={input_name}")
                inp.fill(password)
                break
        
        # Look for submit button
        buttons = sonic_page.query_selector_all("button, input[type='submit']")
        print(f"\nFound {len(buttons)} buttons/submit inputs")
        for i, btn in enumerate(buttons):
            btn_type = btn.get_attribute("type") or ""
            btn_text = btn.inner_text() if btn else ""
            print(f"  {i}: type={btn_type}, text={btn_text[:50] if btn_text else ''}")
        
        # Try to submit the form
        for btn in buttons:
            btn_type = btn.get_attribute("type") or ""
            if btn_type == "submit":
                print("\nClicking submit button")
                btn.click()
                break
        else:
            # Try pressing Enter on password field
            for inp in inputs:
                input_type = inp.get_attribute("type") or ""
                if input_type == "password":
                    print("\nPressing Enter on password field")
                    inp.press("Enter")
                    break
        
        # Wait a bit for the page to load
        time.sleep(5)
        
        # Check current URL and title
        print(f"\nAfter login - URL: {sonic_page.url}")
        print(f"After login - Title: {sonic_page.title()}")
        
        # Take screenshot
        sonic_page.screenshot(path="/Users/sirius_bot/.openclaw/workspace/sonic_after_login.png")
        print("\nScreenshot saved to sonic_after_login.png")
        
    browser.close()
