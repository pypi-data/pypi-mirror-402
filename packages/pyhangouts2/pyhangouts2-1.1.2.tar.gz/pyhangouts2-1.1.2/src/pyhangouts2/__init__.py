"""
@brief A Selenium-based Google Chat library.
@author NexusSfan
@copyright GPL-3.0-or-later
"""

# SPDX-FileCopyrightText: 2026 NexusSfan <nexussfan@duck.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from warnings import warn
import time
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import bs4

__version__ = "1.1.2"

__all__ = ["PyHangouts2", "Message", "Space", "StatusError", "NoMessageFoundError", "AuthorizationError"]

def is_string(obj):
    """
    @brief Check if an object is a string/string-like or not
    @param obj An object
    @retval True Object is a string/string-like
    @retval False Object is not a string/string-like
    """
    return isinstance(obj, (bs4.element.NavigableString, str))

def make_msg_str(messagetext):
    """
    @brief Get a `rogmqd` div and get the full text message out of it
    @param messagetext A `BeautifulSoup4` div with class `rogmqd`
    """
    # replies at: wVNE5
    currentmsg = ""
    try:
        for i in messagetext.contents:
            if is_string(i):
                currentmsg += i
            if isinstance(i, bs4.element.Tag):
                if i.name == "img":
                    if i.attrs.get("alt"):
                        currentmsg += i.attrs["alt"]
                if i.name == "b":
                    if i.string:
                        currentmsg += i.string
                    elif isinstance(i.contents, list):
                        for element in i.contents:
                            if is_string(element):
                                currentmsg += f"*{element.string}*"
                if i.name == "i":
                    if i.string:
                        currentmsg += i.string
                    elif isinstance(i.contents, list):
                        for element in i.contents:
                            if is_string(element):
                                currentmsg += f"_{element.string}_"
                if i.name == "s":
                    if i.string:
                        currentmsg += i.string
                    elif isinstance(i.contents, list):
                        for element in i.contents:
                            if is_string(element):
                                currentmsg += f"~{element.string}~"
                if i.name == "code":
                    if i.string:
                        currentmsg += i.string
                    elif isinstance(i.contents, list):
                        for element in i.contents:
                            if is_string(element):
                                currentmsg += f"`{element.string}`"
    except (
        AttributeError
    ) as e:  # AttributeError: 'NoneType' object has no attribute 'contents'
        # this error happens when user sends ONLY image/file
        raise NoMessageFoundError("No messages found.") from e
    return currentmsg

class PyHangouts2:
    """
    @brief A Selenium-based Google Chat library.
    """

    def __init__(self, headless=False):
        """
        @brief Initialize the Selenium browser
        Starts the Selenium webdriver with customization to make it not look like a bot.
        If it looks like a bot then Google will not allow us to sign in.
        @param headless Use headless mode for the browser?
        """
        self.options = webdriver.ChromeOptions()
        if headless:
            warn("Headless mode may not work properly.", FutureWarning)
            self.options.add_argument("--headless=new")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option("useAutomationExtension", False)
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.minimize_window()
        self.is_in_space = False
        self.is_logged_in = False
        self.space = None

    def login(self, method="manual", username=None, password=None):
        """
        @brief Log in the user to Google Chat.
        @warning Automatic login may not work properly.
        @retval StatusError User is already logged in
        @param method Login method, `manual`/`auto`
        @param username For auto login, the username to enter.
        @param password For auto login, the password to enter.
        """
        if self.is_logged_in:
            raise StatusError("User is already logged in")
        self.driver.maximize_window()
        if method == "auto":
            warn("Automatic login may not work properly.", FutureWarning)
            if not username or not password:
                raise AuthorizationError("Authentication info not completely provided.")
            self.driver.get("https://mail.google.com/chat/u/0/#chat/home")
            actions = ActionChains(self.driver)
            actions.send_keys(username).send_keys(Keys.ENTER).perform()
            time.sleep(3)
            actions.send_keys(password).send_keys(Keys.ENTER).perform()
            WebDriverWait(self.driver, 60).until(
                EC.url_matches("https://mail.google.com/chat/u/0/#chat/home")
            )
        elif method == "manual":
            self.driver.get("https://mail.google.com/chat/u/0/#chat/home")
            WebDriverWait(self.driver, 60).until(
                EC.url_matches("https://mail.google.com/chat/u/0/#chat/home")
            )
        else:
            raise SyntaxError("No valid login method provided!")
        self.driver.minimize_window()
        self.is_logged_in = True

    def join(self, space):
        """
        @brief Join a Google Chat space
        @retval StatusError User is not logged in
        @param space Space ID to join
        """
        if not self.is_logged_in:
            raise StatusError("User is not logged in")
        space_url = f"https://mail.google.com/chat/u/0/#chat/{space}"
        self.driver.get(space_url)
        WebDriverWait(self.driver, 60).until(EC.url_matches(space_url))
        self.driver.switch_to.frame(
            self.driver.find_element(by=By.NAME, value="gtn-brain-iframe-id")
        )
        time.sleep(1)
        self.is_in_space = True
        self.space = space

    def leave(self):
        """
        @brief Leave a Google Chat space
        @retval StatusError User is not logged in
        """
        if not self.is_in_space:
            raise StatusError("User is not logged in")
        self.driver.switch_to.default_content()
        self.driver.get("https://mail.google.com/chat/u/0/#chat/home")
        WebDriverWait(self.driver, 60).until(
            EC.url_matches("https://mail.google.com/chat/u/0/#chat/home")
        )
        self.is_in_space = False
        self.space = None

    def ls(self):
        """
        @brief List Spaces
        @retval StatusError User is in a space or not logged in
        """
        if self.is_in_space:
            raise StatusError("User is in a space")
        if not self.is_logged_in:
            raise StatusError("User is not logged in")
        self.driver.switch_to.frame(
            self.driver.find_element(by=By.NAME, value="gtn-brain-iframe-id")
        )
        page_html = self.driver.page_source
        soup = bs4.BeautifulSoup(page_html, "lxml")
        spaces = []
        spacesget = soup.find(
            "div",
            attrs={
                "jsname": "WbL0Ac",
                "role": "list",
                "aria-labelledby": "EWK8Bb-tJHJj",
                "jsaction": "UEEsmf:xO5IE;",
            },
        )
        for i in spacesget.contents:
            spaceid = i.attrs["id"].replace("/SCcFR", "")
            spaceattrs = (
                i.find("div")
                .find("div")
                .find(lambda tag: tag.name == "div" and "jsname" not in tag.attrs)
                .find("div", class_="Tcg1Uc")
                .find("div", class_="zeiL7e")
            )
            spacename = (
                spaceattrs.find("div", class_="WcXjib")
                .find("div", class_="Vb5pDe")
                .string
            )
            spacemsgs = spaceattrs.find("div", class_="ERFjwe").find(
                lambda tag: tag.name == "span" and "Hkj4n" in tag.attrs["class"]
            )
            spacemsg = ""
            spacemsgauthor = ""
            for msg in spacemsgs.contents:
                if isinstance(msg, bs4.element.Tag):
                    spacemsgauthor = msg.string
                    if spacemsgauthor:
                        spacemsgauthor = spacemsgauthor.strip()[:-1]
                if isinstance(msg, bs4.element.NavigableString):
                    spacemsg = msg
            if not spacemsgauthor:
                # in a dm, if other person sends message it doesn't show author
                spacemsgauthor = spacename
            spacemessage = Message(spacemsgauthor, spacemsg)
            spaces.append(Space(spaceid, spacename, spacemessage))
        self.driver.switch_to.default_content()
        return spaces

    def chat(self, message):
        """
        @brief Send a message in a Space
        @retval StatusError User is not in a space
        @param message Message to send as a string
        """
        if not self.is_in_space:
            raise StatusError("User is not in a space")
        typeui = self.driver.find_element(
            by=By.XPATH,
            value='//div[@jsname="yrriRe"]',
        )
        typeui.send_keys(message)
        typeui.send_keys(Keys.RETURN)

    def get_current_msg(self):
        """
        @brief Gets the latest message in the space and outputs a `Message` object.
        @warning This function is a bit buggy, but it works most of the time.
        @retval NoMessageFoundError No messages found
        @retval Message A message
        """
        if not self.is_in_space:
            raise StatusError("User is not in a space")
        page_html = self.driver.page_source
        soup = bs4.BeautifulSoup(page_html, "lxml")
        currentmsg = ""
        messagenode = soup.find_all(class_="rogmqd")[-1]
        messagetext = messagenode.find("div", class_="DTp27d QIJiHb Zc1Emd")
        currentmsg = make_msg_str(messagetext)
        currentauthor = (
            soup.find_all(class_="nzVtF")[-1].find("span").find("span").string
        )
        if currentmsg and currentauthor:
            return Message(author=currentauthor, message=currentmsg)
        raise NoMessageFoundError("No messages found.")

    def list_messages(self):
        """
        @brief Gets all messages in the space as an iterable
        @warning This function is a bit buggy, but it works most of the time.
        @retval StatusError User is not in a space
        """
        if not self.is_in_space:
            raise StatusError("User is not in a space")
        page_html = self.driver.page_source
        soup = bs4.BeautifulSoup(page_html, "lxml")
        divs = soup.find_all("div", class_="F0wyae oGsu4")
        for div in divs:
            msg = ""
            nosend = False
            auth = div.find("span", class_="nzVtF").find("span").find("span").string
            try:
                messagenode = div.find_all(class_="rogmqd")[-1]
                messagetext = messagenode.find("div", class_="DTp27d QIJiHb Zc1Emd")
                msg = make_msg_str(messagetext)
            except NoMessageFoundError:
                nosend = True
            if not nosend:
                yield Message(author=auth, message=msg)

    def end(self):
        """
        @brief Stops the driver and ends the session
        @retval other Failed
        """
        self.driver.quit()


@dataclass
class Message:
    """
    @brief A Google Chat message
    @param author The author of the message
    @param message Content of message
    """

    author: str
    message: str


@dataclass
class Space:
    """
    @brief A Google Chat Space with a message
    @param spaceid ID of the Space
    @param name Display name of the Space
    @param message The latest message from the Space as a `Message` object
    """

    spaceid: str
    name: str
    message: Message


class StatusError(Exception):
    """
    @brief Google Chat status error
    Used for Status errors with the current space and the login status.
    """


class NoMessageFoundError(Exception):
    """
    @brief Message not found
    """


class AuthorizationError(Exception):
    """
    @brief Google Chat authorization error
    """
