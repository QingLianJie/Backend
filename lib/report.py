import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import *
from selenium.webdriver.common.by import By


def auto_report(username: str, password: str):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    with webdriver.Remote(
        command_executor='selenium://localhost:4444',
        desired_capabilities=chrome_options.to_capabilities(),
    ) as driver:
        driver.get("https://cas.hrbeu.edu.cn/cas/login#/")

        driver.find_element_by_xpath('//*[@id="username"]').send_keys(username)
        driver.find_element_by_xpath('//*[@id="password"]').send_keys(password)
        driver.find_element_by_xpath('//*[@id="login-submit"]').click()

        driver.get("http://one.hrbeu.edu.cn/infoplus/form/JCXBBJSP/start")

        WebDriverWait(driver, 10).until(visibility_of_element_located((By.CSS_SELECTOR,
            ".infoplus_view > div:nth-child(1) > table > tbody > tr.xdTableContentRow > td > div > table > tbody > tr:nth-child(3) > td:nth-child(1) > div > font"
        )))

        driver.find_element_by_xpath('//*[@id="V1_CTRL9"]').click()
        driver.find_element_by_xpath('//*[@id="V1_CTRL11"]').send_keys('其他')
        driver.find_element_by_xpath('//*[@id="V1_CTRL18"]').click()

        driver.execute_script('document.querySelector("#V1_CTRL20").value = "06:00"')
        driver.execute_script('document.querySelector("#V1_CTRL22").value = "22:00"')

        driver.find_element_by_xpath('//*[@id="V1_CTRL26"]').send_keys('其他')

        driver.find_element_by_xpath('//*[@id="form_command_bar"]/li[1]').click()

        WebDriverWait(driver, 10).until(visibility_of_element_located((By.CSS_SELECTOR,
            'button.dialog_button.default.fr'
        )))

        driver.find_element_by_css_selector('button.dialog_button.default.fr').click()

        driver.quit()