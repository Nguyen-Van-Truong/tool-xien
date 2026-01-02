# -*- coding: utf-8 -*-
"""
Human-like behavior utilities
Mô phỏng hành vi con người để tránh bot detection
"""

import random
import time
from typing import Union

from selenium.webdriver.remote.webelement import WebElement


def random_delay(min_seconds: float = 0.5, max_seconds: float = 1.5) -> None:
    """
    Random delay để mô phỏng thời gian suy nghĩ của con người
    
    Args:
        min_seconds: Thời gian tối thiểu
        max_seconds: Thời gian tối đa
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def random_pause(base_seconds: float = 1.0, variance: float = 0.5) -> None:
    """
    Pause với biến thiên random
    
    Args:
        base_seconds: Thời gian cơ bản
        variance: Độ biến thiên (+/-)
    """
    delay = base_seconds + random.uniform(-variance, variance)
    delay = max(0.1, delay)  # Ensure minimum delay
    time.sleep(delay)


def human_type(element: WebElement, text: str, 
               wpm: int = 80, 
               mistake_chance: float = 0.02) -> None:
    """
    Type text như người thật với tốc độ thay đổi và có thể có typo
    
    Args:
        element: WebElement để type vào
        text: Text cần type
        wpm: Words per minute (average)
        mistake_chance: Xác suất gõ sai (0.0 - 1.0)
    """
    # Calculate base delay per character (5 chars = 1 word average)
    chars_per_minute = wpm * 5
    base_delay = 60.0 / chars_per_minute
    
    for i, char in enumerate(text):
        # Random delay variation (+/- 50%)
        delay = base_delay * random.uniform(0.5, 1.5)
        
        # Occasional longer pause (thinking)
        if random.random() < 0.05:
            delay += random.uniform(0.2, 0.5)
        
        # Simulate typo and correction (disabled for now - can cause issues)
        # if random.random() < mistake_chance and i < len(text) - 1:
        #     wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
        #     element.send_keys(wrong_char)
        #     time.sleep(random.uniform(0.1, 0.3))
        #     element.send_keys(Keys.BACKSPACE)
        #     time.sleep(random.uniform(0.1, 0.2))
        
        element.send_keys(char)
        time.sleep(delay)


def human_scroll(driver, direction: str = "down", amount: int = 300) -> None:
    """
    Scroll như người thật với smooth animation
    
    Args:
        driver: Selenium WebDriver
        direction: "up" hoặc "down"
        amount: Số pixels
    """
    scroll_amount = amount if direction == "down" else -amount
    
    try:
        driver.execute_script(f"""
            window.scrollBy({{
                top: {scroll_amount},
                behavior: 'smooth'
            }});
        """)
        random_delay(0.3, 0.7)
    except:
        pass


def random_mouse_movement(driver) -> None:
    """
    Di chuyển chuột random để tạo hoạt động
    (Không thực sự di chuyển chuột - chỉ trigger events)
    """
    try:
        driver.execute_script("""
            const event = new MouseEvent('mousemove', {
                clientX: Math.random() * window.innerWidth,
                clientY: Math.random() * window.innerHeight
            });
            document.dispatchEvent(event);
        """)
    except:
        pass
