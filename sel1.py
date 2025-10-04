from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import credentials as cred
import time

def login(driver):
    username = driver.find_element("name", "ACCOUNTNO")
    username.send_keys(cred.username_5)
    password = driver.find_element("name", "USER_PIN")
    password.send_keys(cred.password_5)
    login_btn = driver.find_element("xpath", "//input[@value='Log In']")
    login_btn.click()


def enter_trade(driver, stock_name, stock_symbol, order_type='buy', qty=1):
    wait = WebDriverWait(driver, 10)
    trade_btn = driver.find_element("xpath", "//a[@class='parent' and text()='TRADE']")
    trade_btn.click()

    enter_trade = wait.until(EC.element_to_be_clickable(("xpath", "//a[@href='eat.html' and text()='Enter a Trade']")))
    enter_trade.click()
    
    time.sleep(2)
    stock_trade_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@id='aStockTrade']")))
    stock_trade_btn.click()

    search_stock_bar = wait.until(EC.presence_of_element_located(("xpath", "//input[@id='SymbolName']")))
    search_stock_bar.send_keys(stock_name)
    
    results = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.search-result")))
    for r in results:
        ticker = r.find_element("xpath", ".//div/p").text  
        if ticker == stock_symbol:
            r.click()  
            break

    if(order_type == 'buy'):
        buy_btn = driver.find_element("xpath", "//input[@id='rbBuy' and @name='OrderTypeId']")
        buy_btn.click()
    elif(order_type == 'sell'):
        sell_btn = driver.find_element("xpath", "//input[@id='rbSell' and @name='OrderTypeId']")
        sell_btn.click()
    elif(order_type == 'short_sell'):
        short_sell_btn = driver.find_element("xpath", "//input[@id='rbShortSell' and @name='OrderTypeId']")
        short_sell_btn.click()
    elif(order_type == 'short_cover'):
        short_cover_btn = driver.find_element("xpath", "//input[@id='rbShortCover' and @name='OrderTypeId']")
        short_cover_btn.click()
    
    number_of_shares_field = driver.find_element("xpath", "//input[@id='BuySellAmt' and @name='BuySellAmt']")
    number_of_shares_field.send_keys(qty)

    market_order_field = driver.find_element("id", "OrderType")
    select = Select(market_order_field)
    select.select_by_visible_text("Market")

    preview_trade_btn = driver.find_element("xpath", "//button[@class='btnTradeBlue' and text()='Preview Trade']")
    preview_trade_btn.click()

    message = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@style,'background: rgba(255, 0, 0')]/p")))
    print(message.text)


def main():
    driver = webdriver.Chrome()
    driver.get("https://www.stockmarketgame.org/login.html")

    login(driver)

    # account Information
    wait = WebDriverWait(driver, 10)
    account_name = wait.until(EC.presence_of_element_located(("xpath", "//p[@style='font-size: 20px; font-weight: 600;']")))
    print("Account: " + account_name.text)

    # Enter Trade
    enter_trade(driver, "APPLE", "AAPL") #change this to integration with strategy

    # finish
    driver.quit()

if __name__ == "__main__":
    main()