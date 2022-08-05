from tracemalloc import stop
from config import tg_token, exchange, api_key,api_key_secret,dollarquantity,path_to_bot,tp_modifier,tg_chat_id_personal,tg_chat_id_listener
from telegram import Update, ForceReply, message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, ConversationHandler
import threading
import schedule
import time
import cv2
from pytesseract import pytesseract
import re
import os
from pybit import usdt_perpetual

integer = 0


session_auth = usdt_perpetual.HTTP( #instantiate connection to Bybit
    endpoint="https://api.bybit.com",
    api_key=api_key,
    api_secret=api_key_secret
)


def getNumber(texxt,begin,end): #get numbers in text
   return re.findall(r'[\d]*[.][\d]+',texxt[begin:end])[0]

def job():
    global tp_modifier
    print("Checking for new trade commands...")

    try:
        for filename in os.listdir("assets"):
            with open(os.path.join("assets", filename), 'r') as f:
                print('/'+f.name)
                filename = f.name
                img = cv2.imread(f.name)
                imagem = cv2.bitwise_not(img) #invert image for more readability
                text = pytesseract.image_to_string(imagem) #convert image to text
                print(text)
                side = ""
                indexer = 0

            if text.find("BUY") > 0: #check if buy order or sell order
                side = "Buy"
                tp1 = text.find("TP1")
                tp2 = text.find("TP2")
                tp3 = text.find("TP3")
                tp4 = text.find("OSL")
                if tp4 < 1:
                    tp4 = text.find("QSL")
                entry = text.find("e:")
                entryEnd = text.find(" (w")
                stoploss = text.find("OSL")
                if stoploss < 1:
                    stoploss = text.find("QSL")
                stoplossEnd = text.find("Leverage")
                pairIndex = text.find("/USDT")
                if (text[pairIndex-2]).isupper():
                    print(f"test: {text[pairIndex-3]}")
                    indexer = 2
                if (text[pairIndex-3]).isupper():
                    print(f"test: {text[pairIndex-3]}")
                    indexer = 3
                if (text[pairIndex-4]).isupper():
                    indexer = 4

            else:
                side = "Sell"
                tp1 = text.find("TP1")
                tp2 = text.find("TP2")
                tp3 = text.find("TP3")
                tp4 = text.find("QSL")
                if tp4 < 1:
                    tp4 = text.find("OSL")
                
                entry = text.find("w:")
                entryEnd = text.find(" (w")
                stoploss = text.find("QSL")
                if stoploss < 1:
                    stoploss = text.find("OSL")
                stoplossEnd = text.find("Leverage")
                pairIndex = text.find("/USDT")
                
                tp_modifier = 2 - tp_modifier

                if '\n' in text[pairIndex-1]:
                    print(f"test: {text[pairIndex-3]}")
                    indexer = 0
                if '\n' in text[pairIndex-2]:
                    print(f"test: {text[pairIndex-3]}")
                    indexer = 1
                if '\n' in text[pairIndex-3]:
                    print(f"test: {text[pairIndex-3]}")
                    indexer = 2
                if '\n' in text[pairIndex-4]:
                    indexer = 3

            pairstring = text[pairIndex-indexer:pairIndex] #PAIR
            os.remove(filename)
            newTrade(pairstring,side,8,float(getNumber(text,entry,entryEnd)),tp_modifier*float(getNumber(text,tp1,tp2)),float(getNumber(text,stoploss,stoplossEnd)))
    except Exception as e: print(e)
  


      





def startjob():
    print("Welcome to autoPosition v0.1")
    schedule.every(1).seconds.do(job)
    
def sendMessage(text) -> None:
    try:
        updater = Updater(token=tg_token, use_context=True)
        updater.bot.send_message(chat_id=tg_chat_id_personal,text=text)
    except Exception as e: print(e)



def newTrade(symbol,side,quantity,price,tp,sl):
    integer = 1
    print(f"symbol is {symbol}")
    response = session_auth.public_trading_records(
    symbol=f"{symbol}USDT",
    limit=1
    )
    currentPrice = float(response['result'][0]['price'])
    amountDecimal = str(price)[::-1].find('.')
    print(f"price = {price}")
    print(f"decimal amount is {amountDecimal}")
    baseQuantity = round((dollarquantity/currentPrice),2)

    if price > currentPrice:
        integer = -0.1
    else: integer = 0.1




    
    response = session_auth.place_conditional_order(
    symbol=f"{symbol}USDT",
    order_type="Market",
    side=side,
    qty=baseQuantity,
    price=price,
    base_price=round((price+integer),4),
    stop_px=price,
    time_in_force="GoodTillCancel",
    trigger_by="LastPrice",
    reduce_only=False,
    close_on_trigger=False,
    take_profit=round(tp,4),
    stop_loss=round(sl,4)
    )
    print(response['ret_msg'])

    if response['ret_msg'] == 'OK':
        print("Order placed!")
        sendMessage(f"Order has been sent to the exchange!\nSymbol:{symbol}\nSide:{side}\nTP:{tp}\nSL:{sl}")

    



#newTrade()

def image_handler(update, context):
    file = update.effective_message.photo[-1].file_id
    obj = context.bot.get_file(file)
    obj.download(custom_path=f"{path_to_bot}/assets/trade1.jpg")
    sendMessage("Image received")
    
 


def main() -> None:
    updater = Updater(token=tg_token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.photo,image_handler))
    updater.start_polling()
    updater.bot.send_message(chat_id=tg_chat_id_personal,text=f'Telegram bot started succesfully!!')


try:
    threading.Thread(target=startjob()).start() #start bot thread
    threading.Thread(target=main()).start() #start TG bot thread
except Exception as e: print(e)

while True:
    schedule.run_pending()
    time.sleep(1)
