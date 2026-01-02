# -*- coding: utf-8 -*-
"""
Click helper utilities
Multiple click methods with fallbacks (from v10 logic)
"""

import time
import random
from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains


def scroll_to_element(driver: WebDriver, element: WebElement, block: str = "center") -> bool:
    """
    Scroll element vào view (smooth như người thật)
    
    Args:
        driver: Selenium WebDriver
        element: Element cần scroll tới
        block: Position ("start", "center", "end")
        
    Returns:
        True nếu thành công
    """
    try:
        driver.execute_script(f"""
            arguments[0].scrollIntoView({{
                block: '{block}',
                behavior: 'smooth'
            }});
        """, element)
        time.sleep(random.uniform(0.3, 0.7))
        return True
    except:
        return False


def hover_element(driver: WebDriver, element: WebElement) -> bool:
    """
    Hover chuột lên element
    
    Args:
        driver: Selenium WebDriver
        element: Element cần hover
        
    Returns:
        True nếu thành công
    """
    try:
        ActionChains(driver).move_to_element(element).pause(
            random.uniform(0.2, 0.4)
        ).perform()
        return True
    except:
        return False


def click_element(
    driver: WebDriver, 
    element: WebElement,
    scroll_first: bool = True,
    hover_first: bool = True
) -> tuple[bool, str]:
    """
    Click element với multiple fallback methods (từ v10)
    
    Methods:
    1. ActionChains với mouse movement (human-like)
    2. JavaScript mouse events (simulate real click)
    3. Regular click()
    4. JavaScript click (last resort)
    
    Args:
        driver: Selenium WebDriver
        element: Element cần click
        scroll_first: Scroll tới element trước
        hover_first: Hover lên element trước
        
    Returns:
        Tuple (success: bool, method_used: str)
    """
    errors = []
    
    # Pre-click: Scroll và hover (human-like)
    if scroll_first:
        scroll_to_element(driver, element)
    
    if hover_first:
        hover_element(driver, element)
    
    # Method 1: ActionChains với mouse movement (most human-like)
    try:
        ActionChains(driver).move_to_element(element).pause(
            random.uniform(0.1, 0.3)
        ).click().perform()
        return True, "ActionChains"
    except Exception as e:
        errors.append(f"ActionChains: {e}")
    
    # Method 2: JavaScript mouse events (simulate real click)
    try:
        driver.execute_script("""
            var element = arguments[0];
            var rect = element.getBoundingClientRect();
            var x = rect.left + rect.width / 2;
            var y = rect.top + rect.height / 2;
            
            var mouseDown = new MouseEvent('mousedown', {
                view: window, bubbles: true, cancelable: true,
                clientX: x, clientY: y
            });
            var mouseUp = new MouseEvent('mouseup', {
                view: window, bubbles: true, cancelable: true,
                clientX: x, clientY: y
            });
            var click = new MouseEvent('click', {
                view: window, bubbles: true, cancelable: true,
                clientX: x, clientY: y
            });
            
            element.dispatchEvent(mouseDown);
            element.dispatchEvent(mouseUp);
            element.dispatchEvent(click);
        """, element)
        time.sleep(0.2)
        return True, "JS_MouseEvents"
    except Exception as e:
        errors.append(f"JS_MouseEvents: {e}")
    
    # Method 3: Regular click (fallback)
    try:
        element.click()
        return True, "Regular"
    except Exception as e:
        errors.append(f"Regular: {e}")
    
    # Method 4: Simple JavaScript click (last resort)
    try:
        driver.execute_script("arguments[0].click();", element)
        return True, "JS_Click"
    except Exception as e:
        errors.append(f"JS_Click: {e}")
    
    # All methods failed
    return False, f"All failed: {errors}"


def double_click(driver: WebDriver, element: WebElement) -> bool:
    """
    Double-click element
    
    Args:
        driver: Selenium WebDriver
        element: Element cần double-click
        
    Returns:
        True nếu thành công
    """
    try:
        ActionChains(driver).double_click(element).perform()
        return True
    except:
        try:
            driver.execute_script("""
                var element = arguments[0];
                var event = new MouseEvent('dblclick', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                });
                element.dispatchEvent(event);
            """, element)
            return True
        except:
            return False


def click_at_position(driver: WebDriver, x: int, y: int) -> bool:
    """
    Click tại vị trí x, y
    
    Args:
        driver: Selenium WebDriver
        x: X coordinate
        y: Y coordinate
        
    Returns:
        True nếu thành công
    """
    try:
        driver.execute_script(f"""
            var event = new MouseEvent('click', {{
                bubbles: true,
                cancelable: true,
                view: window,
                clientX: {x},
                clientY: {y}
            }});
            document.elementFromPoint({x}, {y}).dispatchEvent(event);
        """)
        return True
    except:
        return False
