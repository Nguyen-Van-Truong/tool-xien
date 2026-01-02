# -*- coding: utf-8 -*-
"""
Element finder utilities
Tìm elements với retry và multiple selectors
"""

import time
from typing import Optional, List, Union

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def wait_for_element(
    driver: WebDriver,
    selector: str,
    by: By = By.CSS_SELECTOR,
    timeout: int = 10,
    visible: bool = True
) -> Optional[WebElement]:
    """
    Đợi element xuất hiện với timeout
    
    Args:
        driver: Selenium WebDriver
        selector: CSS selector hoặc XPath
        by: Loại selector (By.CSS_SELECTOR, By.XPATH, etc.)
        timeout: Số giây timeout
        visible: True = đợi visible, False = đợi presence
        
    Returns:
        WebElement hoặc None
    """
    try:
        wait = WebDriverWait(driver, timeout)
        if visible:
            element = wait.until(
                EC.visibility_of_element_located((by, selector))
            )
        else:
            element = wait.until(
                EC.presence_of_element_located((by, selector))
            )
        return element
    except TimeoutException:
        return None
    except Exception:
        return None


def wait_for_any_element(
    driver: WebDriver,
    selectors: List[str],
    by: By = By.CSS_SELECTOR,
    timeout: int = 10
) -> Optional[WebElement]:
    """
    Đợi bất kỳ element nào trong list xuất hiện
    
    Args:
        driver: Selenium WebDriver
        selectors: List CSS selectors
        timeout: Số giây timeout
        
    Returns:
        WebElement đầu tiên tìm thấy hoặc None
    """
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        for selector in selectors:
            try:
                element = driver.find_element(by, selector)
                if element and element.is_displayed():
                    return element
            except:
                continue
        time.sleep(0.5)
    
    return None


def find_button_by_text(
    driver: WebDriver,
    texts: List[str],
    tags: List[str] = None,
    case_sensitive: bool = False
) -> Optional[WebElement]:
    """
    Tìm button/link theo text content
    
    Args:
        driver: Selenium WebDriver
        texts: List text cần tìm (tìm theo thứ tự ưu tiên)
        tags: List tag names (default: button, a)
        case_sensitive: So sánh case-sensitive
        
    Returns:
        WebElement hoặc None
    """
    tags = tags or ['button', 'a']
    
    for tag in tags:
        try:
            elements = driver.find_elements(By.TAG_NAME, tag)
            for element in elements:
                try:
                    if not element.is_displayed():
                        continue
                    
                    # Get text from multiple sources
                    elem_text = (
                        element.text or 
                        element.get_attribute("textContent") or 
                        element.get_attribute("innerText") or 
                        ""
                    ).strip()
                    
                    if not elem_text:
                        continue
                    
                    compare_text = elem_text if case_sensitive else elem_text.lower()
                    
                    for search_text in texts:
                        search = search_text if case_sensitive else search_text.lower()
                        if search in compare_text or compare_text == search:
                            return element
                            
                except:
                    continue
        except:
            continue
    
    return None


def find_input_by_type(
    driver: WebDriver,
    input_type: str,
    visible_only: bool = True
) -> Optional[WebElement]:
    """
    Tìm input theo type (email, password, text, etc.)
    
    Args:
        driver: Selenium WebDriver
        input_type: Type của input
        visible_only: Chỉ tìm visible elements
        
    Returns:
        WebElement hoặc None
    """
    selectors = [
        f'input[type="{input_type}"]',
        f'input[type="{input_type.upper()}"]',
    ]
    
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                if visible_only and not elem.is_displayed():
                    continue
                return elem
        except:
            continue
    
    return None


def is_visible(element: WebElement) -> bool:
    """
    Check xem element có visible không
    
    Args:
        element: WebElement
        
    Returns:
        True nếu visible
    """
    try:
        return element.is_displayed()
    except:
        return False


def get_element_text(element: WebElement) -> str:
    """
    Lấy text từ element (thử nhiều cách)
    
    Args:
        element: WebElement
        
    Returns:
        Text content
    """
    try:
        text = element.text
        if text:
            return text.strip()
        
        text = element.get_attribute("textContent")
        if text:
            return text.strip()
        
        text = element.get_attribute("innerText")
        if text:
            return text.strip()
        
        text = element.get_attribute("value")
        if text:
            return text.strip()
            
        return ""
    except:
        return ""
