# Instagram Account Search Automation
# Version 2.0
#
# Reads search terms from input.txt
# Searches Instagram for each term
# Saves returned usernames to output.txt

# =========================
# IMPORTS
# =========================

from pathlib import Path
from time import sleep
from random import randint
from urllib.parse import quote

from selenium import webdriver
from selenium.webdriver.edge.service import Service

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from stdiomask import getpass


# =========================
# FILE LOCATIONS
# =========================

PROJECT_ROOT = Path(__file__).resolve().parent

INPUT_FILE = PROJECT_ROOT / "input.txt"
OUTPUT_FILE = PROJECT_ROOT / "output.txt"

DRIVER = str(PROJECT_ROOT / "Driver" / "msedgedriver.exe")

EDGE = r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"

INSTAGRAM = "https://www.instagram.com"


# =========================
# SETTINGS
# =========================

WAIT_TIME = 5

# Wait between searches.
# CHANGE: Lines 45-46
MIN_SEARCH_WAIT = 2
MAX_SEARCH_WAIT = 4


# =========================
# READ INPUT FILE
# =========================

# CHANGE: New block
if not INPUT_FILE.exists():
    print("ERROR: input.txt was not found.")
    input("Press Enter to exit...")
    quit()


with open(INPUT_FILE, "r", encoding="utf-8") as file:
    SEARCH_TERMS = [
        line.strip()
        for line in file.readlines()
        if line.strip()
    ]


if not SEARCH_TERMS:
    print("ERROR: input.txt is empty.")
    input("Press Enter to exit...")
    quit()


print(f"Loaded {len(SEARCH_TERMS)} search terms.")


# =========================
# EDGE OPTIONS
# =========================

Edge_Options = webdriver.EdgeOptions()

Edge_Options.add_argument("--inprivate")

# CHANGE: Removed the previous automation-hiding options.
# They are not required for searching accounts.

Edge_Options.binary_location = EDGE


# =========================
# START BROWSER
# =========================

service = Service(executable_path=DRIVER)

Browser = webdriver.Edge(
    service=service,
    options=Edge_Options
)


# =========================
# HELPER FUNCTIONS
# =========================

def random_wait():
    """
    Wait for a short random period.
    """

    sleep(randint(
        MIN_SEARCH_WAIT,
        MAX_SEARCH_WAIT
    ))


def load_existing_results():
    """
    Load usernames already in output.txt.
    """

    if not OUTPUT_FILE.exists():
        return set()

    with open(OUTPUT_FILE, "r", encoding="utf-8") as file:
        return {
            line.strip()
            for line in file.readlines()
            if line.strip()
        }


def save_username(username):
    """
    Add one username to output.txt.
    """

    with open(OUTPUT_FILE, "a", encoding="utf-8") as file:
        file.write(username + "\n")


def get_username_from_url(url):
    """
    Extract a username from an Instagram profile URL.

    Example:
    https://www.instagram.com/example/
    becomes:
    example
    """

    if not url:
        return None

    # Remove query parameters.
    url = url.split("?")[0]

    # Remove trailing slash.
    url = url.rstrip("/")

    # Make sure this is an Instagram URL.
    if "instagram.com/" not in url:
        return None

    username = url.split("instagram.com/")[-1]

    # Instagram pages which are not user profiles.
    ignored_pages = {
        "accounts",
        "about",
        "direct",
        "directory",
        "emails",
        "explore",
        "legal",
        "privacy",
        "reels",
        "settings",
        "stories",
        "web",
    }

    if username.lower() in ignored_pages:
        return None

    # Ignore URLs containing another path.
    if "/" in username:
        return None

    return username


def search_instagram(search_term):
    """
    Search Instagram and return usernames found in the results.
    """

    print()
    print(f"Searching Instagram for: {search_term}")

    # CHANGE: Open Instagram search directly.
    search_url = (
        "https://www.instagram.com/explore/search/"
        "?q=" + quote(search_term)
    )

    Browser.get(search_url)

    sleep(WAIT_TIME)

    usernames = set()

    # CHANGE: Find Instagram profile links.
    links = Browser.find_elements(
        By.CSS_SELECTOR,
        'a[href^="/"]'
    )

    for link in links:

        try:
            href = link.get_attribute("href")

            username = get_username_from_url(href)

            if username:
                usernames.add(username)

        except Exception:
            continue

    return usernames

# =========================
# LOGIN
# =========================

print()
print("Instagram login")
print("----------------")

USERNAME = input("USERNAME: ")
PASSWORD = getpass("PASSWORD: ", "*")


Browser.get(INSTAGRAM)


# =========================
# COOKIE POP-UP
# =========================

# CHANGE: Added cookie pop-up handling before looking for the login fields.

try:
    Cookie_Wait = WebDriverWait(Browser, WAIT_TIME)

    Cookie_Button = Cookie_Wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[contains(text(),'Allow') "
                "or contains(text(),'Accept') "
                "or contains(text(),'allow') "
                "or contains(text(),'accept')]"
            )
        )
    )

    Cookie_Button.click()

    random_wait()

    print("Cookie pop-up dismissed")

except Exception:
    print("No cookie pop-up found")


# =========================
# FIND LOGIN PAGE
# =========================

try:

    # CHANGE: This now runs AFTER the cookie handling above.
    Username_Input_Element = WebDriverWait(
        Browser,
        WAIT_TIME
    ).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='text']")
        )
    )

    print("Login page found.")

except Exception as Error:

    print("Could not find the Instagram login page.")
    print(f"Error: {Error}")

    Browser.quit()

    input("Press Enter to exit...")
    quit()


Username_Input_Element.send_keys(USERNAME)


Password_Input_Element = Browser.find_element(
    By.CSS_SELECTOR,
    "input[type='password']"
)

Password_Input_Element.send_keys(PASSWORD)

Password_Input_Element.send_keys(Keys.ENTER)


# =========================
# MANUAL VERIFICATION
# =========================

print()
print("If Instagram asks for a verification code,")
print("enter it in the browser.")

input(
    "Press Enter here when you are logged in "
    "and ready to continue..."
)



# =========================
# LOAD EXISTING RESULTS
# =========================

Found_Usernames = load_existing_results()

print()
print(f"Existing usernames in output.txt: {len(Found_Usernames)}")


# =========================
# SEARCH
# =========================

try:

    for Search_Term in SEARCH_TERMS:

        try:

            Results = search_instagram(Search_Term)

            print(
                f"Instagram returned {len(Results)} "
                f"possible account(s)."
            )

            New_Results = 0

            for username in Results:

                if username not in Found_Usernames:

                    save_username(username)

                    Found_Usernames.add(username)

                    New_Results += 1

                    print(f"  + {username}")

            print(
                f"Added {New_Results} new username(s)."
            )

            random_wait()

        except Exception as Error:

            print(
                f"ERROR while searching for "
                f"'{Search_Term}': {Error}"
            )

            continue


finally:

    Browser.quit()


# =========================
# FINISHED
# =========================

print()
print("==============================")
print("SEARCH COMPLETE")
print("==============================")
print(f"Total usernames: {len(Found_Usernames)}")
print(f"Saved to: {OUTPUT_FILE}")
print("==============================")

input("Press Enter to exit...")