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
    options = webdriver.ChromeOptions()
    options.headless = background
    
    # Random viewport with aspect ratio maintained
    if viewports:
        viewport = choice(viewports)
        width, height = map(int, viewport.split(','))
        # Slightly randomize dimensions while maintaining aspect ratio
        width = width + randint(-50, 50)
        height = int(height * (width / int(viewport.split(',')[0])))
        options.add_argument(f"--window-size={width},{height}")
    
    # Enhanced anti-detection measures
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-infobars")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-site-isolation-trials")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-popup-blocking")
    
    # Random timezone and geolocation
    timezones = ['America/New_York', 'Europe/London', 'Asia/Tokyo', 'Australia/Sydney', 'Europe/Paris']
    options.add_argument(f"--timezone={choice(timezones)}")
    
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Enhanced preferences
    prefs = {
        "intl.accept_languages": 'en_US,en',
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.default_content_setting_values.notifications": 2,
        "download_restrictions": 3,
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.images": 1,
        "profile.default_content_setting_values.cookies": 1,
        "profile.default_content_setting_values.plugins": 1,
        "profile.default_content_setting_values.geolocation": randint(0, 1),
        "profile.default_content_setting_values.media_stream_mic": 1,
        "profile.default_content_setting_values.media_stream_camera": 1,
        "profile.default_content_settings.javascript": 1,
        "profile.content_settings.exceptions.plugins.*,*.per_resource.adobe-flash-player": 1,
        "profile.content_settings.exceptions.plugins.*,*.per_resource.pdf_viewer": 1
    }
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option('extensionLoadTimeout', 120000)
    
    # Randomize user agent components
    if not agent:
        platforms = ['Windows NT 10.0', 'Windows NT 11.0', 'Macintosh; Intel Mac OS X 10_15_7']
        browsers = ['Chrome/120.0.0.0', 'Chrome/119.0.0.0', 'Chrome/118.0.0.0']
        agent = f"Mozilla/5.0 ({choice(platforms)}) AppleWebKit/537.36 (KHTML, like Gecko) {choice(browsers)} Safari/537.36"
    options.add_argument(f"user-agent={agent}")
    
    options.add_argument("--mute-audio")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-features=UserAgentClientHint')
    options.add_argument("--disable-web-security")
    
    # Additional WebDriver settings
    webdriver.DesiredCapabilities.CHROME['loggingPrefs'] = {
        'driver': 'OFF', 'server': 'OFF', 'browser': 'OFF'
    }

    if not background:
        options.add_extension(WEBRTC)
        options.add_extension(FINGERPRINT)
        options.add_extension(ACTIVE)
        
        # Add custom extensions
        if CUSTOM_EXTENSIONS:
            for extension in CUSTOM_EXTENSIONS:
                options.add_extension(extension)

    if auth_required:
        create_proxy_folder(proxy, proxy_folder)
        options.add_argument(f"--load-extension={proxy_folder}")
    else:
        options.add_argument(f'--proxy-server={proxy_type}://{proxy}')

    service = Service(executable_path=path)
    driver = webdriver.Chrome(service=service, options=options)
    
    # Execute JavaScript to modify navigator properties
    driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
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

    return driver


def type_keyword(driver, keyword, retry=False):
    if retry:
        for _ in range(30):
            try:
                # Add random mouse movement before clicking
                search_box = driver.find_element(By.CSS_SELECTOR, 'input#search')
                driver.execute_script("""
                    function simulateMouseMovement(element) {
                        const rect = element.getBoundingClientRect();
                        const x = rect.left + rect.width/2;
                        const y = rect.top + rect.height/2;
                        
                        // Create smooth movement
                        let currentX = Math.random() * window.innerWidth;
                        let currentY = Math.random() * window.innerHeight;
                        
                        const steps = 10;
                        const stepX = (x - currentX) / steps;
                        const stepY = (y - currentY) / steps;
                        
                        for(let i = 0; i < steps; i++) {
                            currentX += stepX + (Math.random() - 0.5) * 10;
                            currentY += stepY + (Math.random() - 0.5) * 10;
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
                sleep(uniform(2, 4))  # Randomized sleep

    input_keyword = driver.find_element(By.CSS_SELECTOR, 'input#search')
    input_keyword.clear()
    
    # Type with human-like variations
    for letter in keyword:
        input_keyword.send_keys(letter)
        sleep(uniform(0.1, 0.4))  # Random delay between keystrokes
        if random() < 0.05:  # 5% chance of a typo
            typo = choice(keyword)
            input_keyword.send_keys(typo)
            sleep(uniform(0.5, 1.0))  # Pause to "notice" typo
            input_keyword.send_keys(Keys.BACKSPACE)
            sleep(uniform(0.2, 0.5))
            input_keyword.send_keys(letter)  # Correct the typo

    # Random pause before searching
    sleep(uniform(0.5, 2.0))

    # Randomize search method
    method = randint(1, 3)
    if method == 1:
        input_keyword.send_keys(Keys.ENTER)
    elif method == 2:
        icon = driver.find_element(By.XPATH, '//button[@id="search-icon-legacy"]')
        ensure_click(driver, icon)
    else:
        # Sometimes move mouse around before clicking
        driver.execute_script("""
            const icon = document.querySelector('#search-icon-legacy');
            if (icon) {
                simulateMouseMovement(icon);
            }
        """)
        icon = driver.find_element(By.XPATH, '//button[@id="search-icon-legacy"]')
        ensure_click(driver, icon)


def play_video(driver):
    # Add random initial delay before interacting
    sleep(uniform(1, 3))
    
    try:
        # First check if video is already playing
        try:
            pause_button = driver.find_element(By.CSS_SELECTOR, '[title^="Pause (k)"]')
            # Video is playing, randomly decide to pause
            if random() < 0.2:  # 20% chance to pause
                pause_button.click()
                sleep(uniform(2, 5))
                driver.find_element(By.CSS_SELECTOR, '[title^="Play (k)"]').click()
        except WebDriverException:
            # Video is not playing, try different play methods
            try:
                # Try clicking the large play button
                play_button = driver.find_element(By.CSS_SELECTOR, 'button.ytp-large-play-button.ytp-button')
                driver.execute_script("arguments[0].scrollIntoView(true);", play_button)
                sleep(uniform(0.5, 1.5))
                play_button.send_keys(Keys.ENTER)
            except WebDriverException:
                try:
                    # Try the regular play button
                    play_button = driver.find_element(By.CSS_SELECTOR, '[title^="Play (k)"]')
                    driver.execute_script("arguments[0].scrollIntoView(true);", play_button)
                    sleep(uniform(0.3, 1.0))
                    play_button.click()
                except WebDriverException:
                    # Last resort: JavaScript click
                    driver.execute_script(
                        "document.querySelector('button.ytp-play-button.ytp-button').click()"
                    )

        # Randomly interact with the video player
        if random() < 0.3:  # 30% chance
            try:
                # Random scroll
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
