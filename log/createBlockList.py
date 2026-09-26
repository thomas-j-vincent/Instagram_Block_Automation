
# Modules
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.edge.service import Service         # for microsoft edge
#from selenium.webdriver.chrome.service import Service      #for google chrome

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from time import sleep

from random import choice, randint

from os import listdir

from stdiomask import getpass
print("working...")
from datetime import datetime

from json import loads

# Vars
PROJECT_ROOT = Path(__file__).resolve().parent
RES_DIR = PROJECT_ROOT / 'res'
LOG_DIR = PROJECT_ROOT / 'log'

with open(RES_DIR / 'config.json', 'r', encoding='utf-8') as File_Obj:
    Config_Json = File_Obj.read()

Config = loads(Config_Json)

Buffer = Config['Buffer']
Standard_Wait = Config['Standard_Wait']
Increased_Wait = Config['Increased_Wait']
Buffer_Wait_Lower = Config["Buffer_Wait_Lower"]
Buffer_Wait_Upper = Config["Buffer_Wait_Upper"]
Match_Mode = Config.get('Match_Mode', 'exact').lower()
Block_Phrases = [phrase.strip().lower() for phrase in Config.get('Block_Phrases', []) if phrase and phrase.strip()]

DRIVER = str(PROJECT_ROOT / 'Driver' / 'msedgedriver.exe')                      #for microsoft edge
#DRIVER = str(PROJECT_ROOT / 'Driver' / 'chromedriver.exe')                     #for google chrome
EDGE = r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
#BRAVE = r"C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"  for Brave
# CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"             for chrome
LINK = "https://www.instagram.com"
PROFILE = "https://www.instagram.com/{0}"

USERNAME = str(input("USERNAME: "))
PASSWORD = getpass("PASSWORD: ", '*')

Random_Wait_Times = [x/1000 for x in range(2000, 6001)]

Blocked_List_Exists = False
accounts = []

if f'{USERNAME}.txt' in listdir(LOG_DIR):
    Blocked_List_Exists = True


def Filter_Users_By_Match_Mode(users):
    if Match_Mode == 'contains':
        if not Block_Phrases:
            return []
        return [user for user in users if any(phrase in user.lower() for phrase in Block_Phrases)]
    return users


with open(RES_DIR / 'Accounts_To_Block.txt', 'r', encoding='utf-8') as File_Obj:
    To_Block = Filter_Users_By_Match_Mode([user.strip() for user in File_Obj.readlines() if user.strip()])

Counter = 0
WaitTime = randint(Buffer_Wait_Lower, Buffer_Wait_Upper)

# XPATH Vars
with open(RES_DIR / 'xpath.json', 'r', encoding='utf-8') as File_Obj:
    XPATHS_Json = File_Obj.read()

XPATHS = loads(XPATHS_Json)

Search_Button_XPATH = XPATHS["Search_Button_XPATH"]
Three_Dots_XPATH = XPATHS["Three_Dots_XPATH"]
Block_Button_XPATH = XPATHS["Block_Button_XPATH"]
Follow_Button_XPATH = XPATHS["Follow_Button_XPATH"]
Block_Confirm_XPATH = XPATHS["Block_Confirm_XPATH"]

# Edge options
Edge_Options = webdriver.EdgeOptions()  
Edge_Options.add_argument("--inprivate") 
Edge_Options.add_argument("--enable-chrome-browser-cloud-management")
Edge_Options.add_argument("--disable-blink-features=AutomationControlled")   # NEW: reduces automation signals
Edge_Options.add_experimental_option("excludeSwitches", ["enable-automation"])  # NEW: hides the "controlled by automation" bar
Edge_Options.add_experimental_option("useAutomationExtension", False)        # NEW: disables the automation extension
Edge_Options.binary_location = EDGE 

# Chrome Options
#Chrome_Options = webdriver.ChromeOptions()
#Chrome_Options.add_argument("--incognito")
#Chrome_Options.add_argument("--enable-chrome-browser-cloud-management")
#Chrome_Options.binary_location = BRAVE

# Initialisation
service = Service(executable_path=DRIVER)
Browser = webdriver.Edge(service=service, options=Edge_Options)              #for edge
#Browser = webdriver.Chrome(service=service, options=Chrome_Options)         #for chrome
#Browser.execute_script("""                                         # NEW: hides the navigator.webdriver flag
#    Object.defineProperty(navigator, 'webdriver', {
#        get: () => undefined
#    })
#""")

# Functions
def accountsToBlock(List):
    with open('accountsToBlock.txt', 'w', encoding='utf-8') as File_Obj:
        [File_Obj.write(element + '\n') for element in List]

def retriveAccountsToBlock():
    with open('accountsToBlock.txt', 'r', encoding='utf-8') as File_Obj:
        Data = [element.strip('\n') for element in File_Obj.readlines()]
    return Data

def log_error(ERROR):
    Mode = 'a' if f'Error_Log_{USERNAME}.txt' in listdir(LOG_DIR) else 'w'
    with open(LOG_DIR / f'Error_Log_{USERNAME}.txt', Mode, encoding='utf-8') as File_Obj:
        time = datetime.now()
        record_time = f"[{time.day}/{time.month}/{time.year} | {time.time().hour}:{time.time().minute}:{time.time().second}]"
        File_Obj.write(f"{record_time}\n---[Error Start Block]---\n{ERROR}\n---[Error End Block]---\n")

def New_List():
    New = []
    for element in To_Block:
        if element not in accounts:
            New.append(element)
    return New

def RandWait():
    Wait_Time = choice(Random_Wait_Times)
    sleep(Wait_Time)

def Block(USER_LINK):
    Browser.get(USER_LINK)
    
    try:
        WebDriverWait(Browser, Increased_Wait).until(EC.presence_of_element_located((By.XPATH, Three_Dots_XPATH)))
    except Exception as Error:
        print("  -> Stuck on: Three_Dots_XPATH (menu button not found)")
        return "404"
    
    RandWait()
    
    try:
        Follow_Button = Browser.find_element(By.XPATH, Follow_Button_XPATH)
    except Exception as Error:
        print("  -> Stuck on: Follow_Button_XPATH (follow/unblock button not found)")
        return "404"
    
    if str(Follow_Button.text) == "Unblock":
        RandWait()
        return None
    
    RandWait()

    try:                                                            # NEW: separate stage for clicking the three dots
        Three_Dots = Browser.find_element(By.XPATH, Three_Dots_XPATH)
        Three_Dots.click()
    except Exception as Error:
        print("  -> Stuck on: clicking Three_Dots")                 # NEW
        return "404"

    try:                                                            # NEW: separate stage for the block menu option
        WebDriverWait(Browser, Standard_Wait).until(EC.presence_of_element_located((By.XPATH, Block_Button_XPATH)))
    except Exception as Error:
        print("  -> Stuck on: Block_Button_XPATH (menu opened, but Block option not found)")  # NEW
        return "404"
    
    RandWait()

    try:                                                            # NEW: separate stage for clicking Block
        Block_Button = Browser.find_element(By.XPATH, Block_Button_XPATH)
        Block_Button.click()
    except Exception as Error:
        print("  -> Stuck on: clicking Block_Button")               # NEW
        return "404"

    try:                                                            # NEW: separate stage for the confirmation dialog
        WebDriverWait(Browser, Standard_Wait).until(EC.presence_of_element_located((By.XPATH, Block_Confirm_XPATH)))
    except Exception as Error:
        print("  -> Stuck on: Block_Confirm_XPATH (confirmation button not found)")  # NEW
        return "404"

    RandWait()
    
    Block_Confirm = Browser.find_element(By.XPATH, Block_Confirm_XPATH)
    Block_Confirm.click()
    sleep(4)
        
    return True

# Vars
if Blocked_List_Exists:
    accounts = retriveAccountsToBlock()
    To_Block = New_List()
    
# Automation Process
Browser.get(LINK)


try:                                                                # NEW: cookie pop-up handling block, start
    Cookie_Wait = WebDriverWait(Browser, Standard_Wait)
    Cookie_Button = Cookie_Wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Allow')]"))
    )
    Cookie_Button.click()
    RandWait()
    print("Cookie pop-up dismissed")
except Exception as Error:
    print("No cookie pop-up found")                                # NEW: cookie pop-up handling block, end


try:                                                                 # NEW: screenshot-on-failure block, start
    WebDriverWait(Browser, Standard_Wait).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
    print("success!")
except Exception as Error:
    print("stuck finding password")
    #Browser.save_screenshot(str(LOG_DIR / 'login_timeout_debug.png'))  # NEW: saves what the page shows
    raise                                                           # NEW: screenshot-on-failure block, end

#WebDriverWait(Browser, Standard_Wait).until(EC.presence_of_element_located((By.NAME, "password")))
RandWait()

Username_Input_Element = Browser.find_element(By.CSS_SELECTOR, "input[type='text']")
Username_Input_Element.send_keys(USERNAME)

#Password_Input_Element = Browser.find_element(By.NAME, "password")
Password_Input_Element = Browser.find_element(By.CSS_SELECTOR, "input[type='password']")
Password_Input_Element.send_keys(PASSWORD)
RandWait()

Password_Input_Element.send_keys(Keys.ENTER)
input("If Instagram asks for a verification code, enter it in the browser now. Then press Enter here to continue...")  # NEW: unlimited manual pause
WebDriverWait(Browser, Standard_Wait).until(EC.presence_of_element_located((By.XPATH, Search_Button_XPATH)))
RandWait()

print("Press 'Ctrl + c' to stop")

for User in To_Block:
    try:
        Val = Block(PROFILE.format(User))
        if Val == None:
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {User} Already Blocked")
            accounts.append(User)
            Counter += 1

        elif Val == True:
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {User} blocked")
            accounts.append(User)
            Counter += 1
            
        elif Val == "404":
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {User} | Account not found (unable to locate button elements)")
            accounts.append(User)
            Counter += 1
        
        if Counter == Buffer:
            Counter = 0
            sleep(WaitTime)
    
    except KeyboardInterrupt:
        print("[Ctrl + c] received.. stopping now!!")
        accountsToBlock(accounts)
        Browser.quit()
        quit()
    
    except Exception as Error:
        print(Error)
        log_error(Error)
        try:
            Browser.get(LINK)
            WebDriverWait(Browser, Standard_Wait).until(EC.presence_of_element_located((By.XPATH, Search_Button_XPATH)))
            RandWait()
        except Exception as Error_2:
            print(Error_2)
            log_error(Error_2)
            accountsToBlock(accounts)
            quit()

#Quit
sleep(Standard_Wait * 1.5)
Browser.quit()
accountsToBlock(accounts)
