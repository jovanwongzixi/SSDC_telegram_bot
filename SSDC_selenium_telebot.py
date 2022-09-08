# -*- coding: utf-8 -*-
"""
Created on Tue Jan 19 00:23:36 2021

@author: Jovan
"""
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters, ConversationHandler
import logging
from typing import Dict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime
import telegram_token 

#import current datetime
date_time = datetime.datetime.now()
day = date_time.day
month = date_time.month
year = date_time.year
selected_date = date_time.strftime("%d") + " " + date_time.strftime("%b") + " " + date_time.strftime("%Y")

service = Service(executable_path='./chromedriver_win32/chromedriver')
options = Options()
options.add_experimental_option('excludeSwitches', ['enable-logging'])
'''options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--headless")'''
driver = webdriver.Chrome(service=service, options=options)
result_dict = {} 


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
logger = logging.getLogger(__name__)

commandlist_text = '''List of commands
/start Starts the bot
/help Sends list of commands
/scrape to start scraping
/slots display available slots
'''

CHOOSING, TYPING_REPLY = range(2)

reply_keyboard = [
    ['Username', 'Password'],
    ['Done']
    ]

markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

#conversation functions
def dict_to_str(user_data: Dict[str, str]):
    facts = list()

    for key, value in user_data.items():
        facts.append(f'{key} - {value}')

    return "\n".join(facts).join(['\n', '\n'])

def start(update: Update, context:CallbackContext):
    driver.get("https://www.ssdcl.com.sg/User/Login")
    update.message.reply_text("Hi! I'm a SSDC bot scraper! "
                              "Please choose an info to input",
                              reply_markup=markup)
    
    return CHOOSING

def choice(update: Update, context: CallbackContext):
    text = update.message.text
    context.user_data['choice'] = text
    update.message.reply_text(f'Please type in your {text.lower()}!')
    
    return TYPING_REPLY

def user_info(update: Update, context: CallbackContext):
    user_data = context.user_data
    text = update.message.text
    info = user_data['choice']
    user_data[info] = text
    del user_data['choice']
    
    update.message.reply_text("This is what you have told me so far:"
                              f"{dict_to_str(user_data)} \n"
                              "You can change your info, or input something new",
                              reply_markup=markup)
    return CHOOSING

def done(update: Update, context:CallbackContext):
    update.message.reply_text("Done! Press /scrape to start scraping your slots")
    
    return ConversationHandler.END

def commandlist(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=commandlist_text)

def slotsformat(result_dict: Dict[str,list]):
    slot_list = list()
    
    for key, value in result_dict.items():
        slot_list.append(f"{key} - {value}")
        
    return '\n\n'.join(slot_list).join(['\n', '\n'])

def slotscrape(update: Update, context: CallbackContext):
    user_data = context.user_data
    username = driver.find_element_by_id('UserName')
    username.clear()
    username.send_keys(user_data['Username'])
    
    pw = driver.find_element_by_id('Password')
    pw.clear()
    pw.send_keys(user_data['Password'])
    pw.send_keys(Keys.RETURN)

    booking_cancellation = driver.find_element_by_link_text('Booking and Cancellation')
    booking_cancellation.click()
    
    
    new_booking = WebDriverWait(driver, 10).until(
         EC.presence_of_element_located((By.ID, "btnNewBooking"))
    )
    new_booking.click()
        
    checkbox = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "chkProceed"))
        )
    checkbox.click()

    proceed = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "lnkProceed"))
    )
    proceed.click()
    
    booking_type = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//select[@id='BookingType']/option[@value='PL']"))
    )
    booking_type.click()
    
    location = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//select[@id='SelectedLocation']/option[@value='Woodlands']"))
    )
    location.click()

    #get earliest date button removed from website  
    '''get_earliest_date = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "button-searchDate"))
   )
    get_earliest_date.click()'''
    result_dict = {}
    def slot_search(result_dict):
        global selected_date
        lesson_date = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='SelectedDate']"))
        )
        lesson_date.click()
        lesson_date.send_keys(Keys.CONTROL + 'a' + Keys.DELETE)
        lesson_date.send_keys(selected_date)
        #driver.implicitly_wait(30)
        '''availability_check = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.LINK_TEXT, "Check for availability"))
        )'''
        availability_check = driver.find_element_by_link_text("Check for availability")
        availability_check.click()
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//tbody[@class='tr-border-bottom']"))
                                        )
        booking_slots = driver.find_elements_by_xpath("//table[@class='table table-borderless table-striped no-background clear-padding-first-child available-slots-mobile main-table']/tbody[@class='tr-border-bottom']/tr")
        
        slottime_list = []
        result_dict.clear()
        
    
        for i in range(1, len(booking_slots)+1):
            slotdate = driver.find_element_by_xpath(f"//table[@class='table table-borderless table-striped no-background clear-padding-first-child available-slots-mobile main-table']/tbody[@class='tr-border-bottom']/tr[{i}]/th").text.strip()
            slottimes = driver.find_elements_by_xpath(f"//table[@class='table table-borderless table-striped no-background clear-padding-first-child available-slots-mobile main-table']/tbody[@class='tr-border-bottom']/tr[{i}]/td/a")
            slotdate = slotdate.split('\n')
            slotdate = slotdate[0].strip() + " " + slotdate[1].strip()
            result_dict[slotdate] = " "
            for slottime in slottimes:
                slottime = slottime.text.strip()
                slottime = slottime.split('\u2714')[0]
                slottime_list.append(slottime)
                result_dict.update({slotdate:slottime_list})
                slottime_list = []
            print(slotsformat(result_dict))
    
    slot_search(result_dict)
    #self implementation to check earliest slot
    global day, month, year, selected_date
    while list(result_dict.values()) == [' ', ' ', ' ', ' ', ' ', ' ', ' ']:
        day +=7
        if month == 2 and day > 28:
            day = 1
            month +=1
        elif month%2 == 0 and day > 30:
            day = 1
            month +=1
            if month == 13:
                year +=1
                month = 1 
        elif month%2 == 1 and day > 31:
            day = 1
            month +=1
        date_time = datetime.datetime(year, month, day)
        selected_date = date_time.strftime("%d") + " " + date_time.strftime("%b") + " " + date_time.strftime("%Y")
        slot_search(result_dict)
    
    context.bot.send_message(chat_id=update.effective_chat.id, text=slotsformat(result_dict))
    
    #books first available slot    
    selected_slot = driver.find_element_by_xpath("//table[@class='table table-borderless table-striped no-background clear-padding-first-child available-slots-mobile main-table']/tbody[@class='tr-border-bottom']/tr/td/a[1]")
    selected_slot.click()
    
    close_btn =  WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//button[@class='btn btn-general-short']"))
    )
    close_btn.click()
    close_btn.send_keys(Keys.RETURN)
    
    cart_btn =  WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//i[@class='btn btn-shopping-cart fa fa-shopping-cart']"))
    )
    cart_btn.click()
    
    confirm_purchase = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.LINK_TEXT, "Confirm Purchase"))
    )
    #confirm_purchase.click()
    
    #failed to implement payment functionality
    '''
    make_payment = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.LINK_TEXT, "Make Payment"))
    )
    make_payment.click()'''
    

def main(): 
    updater = Updater(token=telegram_token.TOKEN, use_context=True) #telegram API token imported from separate file
    
    dispatcher = updater.dispatcher
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states = {
            CHOOSING:[
                MessageHandler(Filters.regex('^(Username|Password)$'), choice)
                ],
            TYPING_REPLY:[
                MessageHandler(Filters.text & ~(Filters.regex('^Done$') | Filters.command), user_info)
                ]
            },
        fallbacks = [MessageHandler(Filters.regex('^Done$'), done)],
        )
    
    dispatcher.add_handler(conv_handler)
    
    scrape_handler = CommandHandler('scrape', slotscrape)
    dispatcher.add_handler(scrape_handler)
    
    help_handler = CommandHandler('help', commandlist)
    dispatcher.add_handler(help_handler)
    updater.start_polling()

    #herokuapp taken down
    '''PORT = int(os.environ.get("PORT", "8443"))
    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=TOKEN)
    updater.bot.set_webhook("https://ssdc-selenium-telebot.herokuapp.com/{}".format(TOKEN))'''

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
    
if __name__ == '__main__':
    main()    
