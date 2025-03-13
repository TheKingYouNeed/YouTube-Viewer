"""
MIT License

Copyright (c) 2021-2022 MShawon

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import os
from glob import glob

from .features import *

WEBRTC = os.path.join('extension', 'webrtc_control.zip')
ACTIVE = os.path.join('extension', 'always_active.zip')
FINGERPRINT = os.path.join('extension', 'fingerprint_defender.zip')
CUSTOM_EXTENSIONS = glob(os.path.join('extension', 'custom_extension', '*.zip')) + \
    glob(os.path.join('extension', 'custom_extension', '*.crx'))

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException
from random import uniform, choice, random, randint
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tempfile
from fake_useragent import UserAgent


def create_proxy_folder(proxy, folder_name):
    proxy = proxy.replace('@', ':')
    proxy = proxy.split(':')
    manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"22.0.0"
}
 """

    background_js = """
var config = {
        mode: "fixed_servers",
        rules: {
        singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
        },
        bypassList: ["localhost"]
        }
    };
chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
function callbackFn(details) {
    return {
        authCredentials: {
            username: "%s",
            password: "%s"
        }
    };
}
chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
);
""" % (proxy[2], proxy[-1], proxy[0], proxy[1])

    os.makedirs(folder_name, exist_ok=True)
    with open(os.path.join(folder_name, "manifest.json"), 'w') as fh:
        fh.write(manifest_json)

    with open(os.path.join(folder_name, "background.js"), 'w') as fh:
        fh.write(background_js)


def get_driver(background, viewports, agent, auth_required, path, proxy, proxy_type, proxy_folder):
    options = uc.ChromeOptions()
    
    if background:
        options.add_argument('--headless=new')
    
    if viewports:
        viewport = choice(viewports)
        width, height = map(int, viewport.split(','))
        width = width + randint(-50, 50)
        height = int(height * (width / int(viewport.split(',')[0])))
        options.add_argument(f"--window-size={width},{height}")
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    
    # Create a unique user data directory
    user_data_dir = tempfile.mkdtemp()
    options.add_argument(f'--user-data-dir={user_data_dir}')
    
    if agent:
        options.add_argument(f'--user-agent={agent}')
    else:
        options.add_argument(f'--user-agent={UserAgent().random}')
    
    if auth_required:
        create_proxy_folder(proxy, proxy_folder)
        options.add_argument(f"--load-extension={proxy_folder}")
    else:
        options.add_argument(f'--proxy-server={proxy_type}://{proxy}')
    
    try:
        driver = uc.Chrome(
            options=options,
            driver_executable_path=path,
            use_subprocess=True,
            headless=background,  
            version_main=None  
        )
        
        driver.set_page_load_timeout(30)
        
        driver.execute_script("""
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function() {
                const context = originalGetContext.apply(this, arguments);
                if (context && arguments[0] === '2d') {
                    const originalGetImageData = context.getImageData;
                    context.getImageData = function() {
                        const imageData = originalGetImageData.apply(this, arguments);
                        const noise = Math.random() * 0.01;
                        for (let i = 0; i < imageData.data.length; i += 4) {
                            imageData.data[i] = imageData.data[i] + noise;
                        }
                        return imageData;
                    };
                }
                return context;
            };
            
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            window.chrome = {
                runtime: {}
            };
        """)
        
        return driver, user_data_dir
        
    except Exception as e:
        print(f"Error creating undetected driver: {str(e)}")
        raise


def type_keyword(driver, keyword, retry=False):
    if retry:
        for _ in range(30):
            try:
                search_box = driver.find_element(By.CSS_SELECTOR, 'input#search')
                driver.execute_script("""
                    function simulateMouseMovement(element) {
                        const rect = element.getBoundingClientRect();
                        const x = rect.left + rect.width/2;
                        const y = rect.top + rect.height/2;
                        
                        const steps = 10;
                        const stepX = (x - Math.random() * window.innerWidth) / steps;
                        const stepY = (y - Math.random() * window.innerHeight) / steps;
                        
                        for(let i = 0; i < steps; i++) {
                            const currentX = Math.random() * window.innerWidth;
                            const currentY = Math.random() * window.innerHeight;
                            const event = new MouseEvent('mousemove', {
                                view: window,
                                bubbles: true,
                                cancelable: true,
                                clientX: currentX,
                                clientY: currentY
                            });
                            document.dispatchEvent(event);
                        }
                    }
                    simulateMouseMovement(arguments[0]);
                """, search_box)
                search_box.click()
                break
            except WebDriverException:
                sleep(uniform(2, 4))  

    input_keyword = driver.find_element(By.CSS_SELECTOR, 'input#search')
    input_keyword.clear()
    
    for letter in keyword:
        input_keyword.send_keys(letter)
        sleep(uniform(0.1, 0.4))  
        if random() < 0.05:  
            typo = choice(keyword)
            input_keyword.send_keys(typo)
            sleep(uniform(0.5, 1.0))  
            input_keyword.send_keys(Keys.BACKSPACE)
            sleep(uniform(0.2, 0.5))
            input_keyword.send_keys(letter)  

    sleep(uniform(0.5, 2.0))

    method = randint(1, 3)
    if method == 1:
        input_keyword.send_keys(Keys.ENTER)
    elif method == 2:
        icon = driver.find_element(By.XPATH, '//button[@id="search-icon-legacy"]')
        ensure_click(driver, icon)
    else:
        driver.execute_script("""
            const icon = document.querySelector('#search-icon-legacy');
            if (icon) {
                simulateMouseMovement(icon);
            }
        """)
        icon = driver.find_element(By.XPATH, '//button[@id="search-icon-legacy"]')
        ensure_click(driver, icon)


def play_video(driver):
    sleep(uniform(1, 3))
    
    try:
        try:
            pause_button = driver.find_element(By.CSS_SELECTOR, '[title^="Pause (k)"]')
            if random() < 0.2:  
                pause_button.click()
                sleep(uniform(2, 5))
                driver.find_element(By.CSS_SELECTOR, '[title^="Play (k)"]').click()
        except WebDriverException:
            try:
                play_button = driver.find_element(By.CSS_SELECTOR, 'button.ytp-large-play-button.ytp-button')
                driver.execute_script("arguments[0].scrollIntoView(true);", play_button)
                sleep(uniform(0.5, 1.5))
                play_button.send_keys(Keys.ENTER)
            except WebDriverException:
                try:
                    play_button = driver.find_element(By.CSS_SELECTOR, '[title^="Play (k)"]')
                    driver.execute_script("arguments[0].scrollIntoView(true);", play_button)
                    sleep(uniform(0.3, 1.0))
                    play_button.click()
                except WebDriverException:
                    driver.execute_script(
                        "document.querySelector('button.ytp-play-button.ytp-button').click()"
                    )

        if random() < 0.3:  
            try:
                scroll_amount = randint(100, 300)
                driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                sleep(uniform(1, 3))
                driver.execute_script(f"window.scrollBy(0, -{scroll_amount});")
            except Exception:
                pass

    except WebDriverException:
        pass

    skip_again(driver)


def play_music(driver):
    try:
        driver.find_element(
            By.XPATH, '//*[@id="play-pause-button" and @title="Pause"]')
    except WebDriverException:
        try:
            driver.find_element(
                By.XPATH, '//*[@id="play-pause-button" and @title="Play"]').click()
        except WebDriverException:
            driver.execute_script(
                'document.querySelector("#play-pause-button").click()')

    skip_again(driver)


def scroll_search(driver, video_title):
    msg = None
    for i in range(1, 11):
        try:
            section = WebDriverWait(driver, 60).until(EC.visibility_of_element_located(
                (By.XPATH, f'//ytd-item-section-renderer[{i}]')))
            if driver.find_element(By.XPATH, f'//ytd-item-section-renderer[{i}]').text == 'No more results':
                msg = 'failed'
                break

            if len(video_title) == 11:
                find_video = section.find_element(
                    By.XPATH, f'//a[@id="video-title" and contains(@href, "{video_title}")]')
            else:
                find_video = section.find_element(
                    By.XPATH, f'//*[@title="{video_title}"]')

            driver.execute_script(
                "arguments[0].scrollIntoViewIfNeeded();", find_video)
            sleep(1)
            bypass_popup(driver)
            ensure_click(driver, find_video)
            msg = 'success'
            break
        except NoSuchElementException:
            sleep(randint(2, 5))
            WebDriverWait(driver, 30).until(EC.visibility_of_element_located(
                (By.TAG_NAME, 'body'))).send_keys(Keys.CONTROL, Keys.END)

    if i == 10:
        msg = 'failed'

    return msg


def search_video(driver, keyword, video_title):
    try:
        type_keyword(driver, keyword)
    except WebDriverException:
        try:
            bypass_popup(driver)
            type_keyword(driver, keyword, retry=True)
        except WebDriverException:
            raise Exception(
                "Slow internet speed or Stuck at recaptcha! Can't perform search keyword")

    msg = scroll_search(driver, video_title)

    if msg == 'failed':
        bypass_popup(driver)

        filters = driver.find_element(By.CSS_SELECTOR, '#filter-menu button')
        driver.execute_script('arguments[0].scrollIntoViewIfNeeded()', filters)
        sleep(randint(1, 3))
        ensure_click(driver, filters)

        sleep(randint(1, 3))
        sort = WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@title="Sort by upload date"]')))
        ensure_click(driver, sort)

        msg = scroll_search(driver, video_title)

    return msg
