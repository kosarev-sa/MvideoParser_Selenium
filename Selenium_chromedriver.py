import time
from pymongo import MongoClient
from pprint import pprint

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
import selenium.common.exceptions as s_exceptions


def get_chrome_driver(site_url):
    chrome_options = Options()
    chrome_options.add_argument('start-maximized')
    driver = webdriver.Chrome(executable_path='./chromedriver.exe', options=chrome_options)
    driver.get(site_url)
    return driver


def get_news(driver):
    new_goods = driver.find_element_by_tag_name('mvid-shelf-group')
    actions = ActionChains(driver)
    actions.move_to_element(new_goods)
    actions.perform()                       # Прокручиваем страницу до блока с новинками

    time.sleep(2)
    first_price = driver.find_element_by_xpath('//mvid-shelf-group[1]/mvid-carousel[1]/div[1]/div[1]/'
                                             'mvid-product-cards-group[1]/div[6]/mvid-price-2[1]/div[1]/div[1]/span[1]')
    actions = ActionChains(driver)
    actions.move_to_element(first_price)    # Прокручиваем страницу ниже до подгрузившихся цен,
    actions.perform()                       # чтобы появилась кнопка для промотки вправо к остальным новинкам

    while True:
        try:                                # Открываем все новинки
            wait = WebDriverWait(driver, 10)
            button = wait.until(EC.element_to_be_clickable((By.XPATH,
                    "//mvid-carousel[@class='carusel ng-star-inserted']/*/button/mvid-icon[@type='chevron_right']"))
                                )
            button.click()
        except s_exceptions.TimeoutException:
            break
        except s_exceptions.ElementNotInteractableException:
            break

        set_of_goods = driver.find_element_by_xpath('//mvid-root[1]/div[1]/ng-component[1]/mvid-layout[1]/div[1]/'
                        'main[1]/div[1]/mvid-shelf-group[1]/mvid-carousel[1]/div[1]/div[1]/mvid-product-cards-group[1]')

        set_goods_all_info_str = set_of_goods.text  # Вся информация о новинках в одну строку (для проверки количества
                                                    # или получения доп. информации, например, об отзывах или бонусах)

        goods_names = driver.find_elements_by_xpath("//mvid-shelf-group[1]/mvid-carousel[1]/div[1]/div[1]/"
                                "mvid-product-cards-group[1]/div[@class='product-mini-card__name ng-star-inserted']")
        goods_prices = driver.find_elements_by_xpath("//mvid-shelf-group[1]/mvid-carousel[1]/div[1]/div[1]/"
                                "mvid-product-cards-group[1]/div[@class='product-mini-card__price ng-star-inserted']")
        goods_images = driver.find_elements_by_xpath("//mvid-shelf-group[1]/mvid-carousel[1]/div[1]/div[1]/"
                            "mvid-product-cards-group[1]/div[@class='product-mini-card__image ng-star-inserted']//img")

        new_goods_lst = []
        for i in range(len(goods_names)):
            good = {}
            good['name'] = goods_names[i].text
            good['price'] = goods_prices[i].text
            good['image'] = goods_images[i].get_attribute('srcset').split(" ")[-2]
            new_goods_lst.append(good)
        new_goods_lst.append(dict(set_goods_all_info=set_goods_all_info_str))

        return new_goods_lst


def news_to_mongo(dbcollection_for_add):                        # функция, записывающаю собранные новинки в созданную БД
    dbcollection_for_add.insert_many(get_news(driver=get_chrome_driver('https://mvideo.ru/')))
    return dbcollection_for_add


def update_and_add_news(dbcollection_for_update_or_add):               # функция, которая добавляет в базу данных только
    for new_good in get_news(driver=get_chrome_driver('https://mvideo.ru/')):   # свежие новинки и обновляет старые
        dbcollection_for_update_or_add.update_one({'name': new_good['name']}, {'$set': new_good}, upsert=True)
    return dbcollection_for_update_or_add


client = MongoClient('127.0.0.1', 27017)
db = client['new_goods']
mvideo = db.mvideo

# news_to_mongo(mvideo)
# for item in mvideo.find({}):
#     pprint(item)

# update_and_add_news(mvideo)
# for item in mvideo.find({}):
#     pprint(item)


# Вариант собранной БД:

# {'_id': ObjectId('61debc0d519814cbd664beb0'),
#  'image': '//img.mvideo.ru/Pdb/30061196b.jpg',
#  'name': 'Смартфон Xiaomi 11 Lite 5G NE 256GB Peach Pink',
#  'price': '34 999 \n39 999 '}
# {'_id': ObjectId('61debc0d519814cbd664beb1'),
#  'image': '//img.mvideo.ru/Pdb/10029602b.jpg',
#  'name': 'Колонка умная Xiaomi Mi Smart Speaker (QBH4221RU)',
#  'price': '4 999 '}
# {'_id': ObjectId('61debc0d519814cbd664beb2'),
#  'image': '//img.mvideo.ru/Pdb/30060723b.jpg',
#  'name': 'Ноутбук HUAWEI MateBook D 15 BoD-WDH9 8+512GB Space Grey',
#  'price': '63 999 '}
# {'_id': ObjectId('61debc0d519814cbd664beb3'),
#  'image': '//img.mvideo.ru/Pdb/6016151b.jpg',
#  'name': 'Подписка M.Prime на 1 месяц + Яндекс.Плюс',
#  'price': '499 \n599 '}
# {'_id': ObjectId('61debc0d519814cbd664beb4'),
#  'image': '//img.mvideo.ru/Pdb/20078495b.jpg',
#  'name': 'Триммер Philips QP2510/11',
#  'price': '2 599 '}
# {'_id': ObjectId('61debc0d519814cbd664beb5'),
#  'image': '//img.mvideo.ru/Pdb/20077617b.jpg',
#  'name': 'Электробритва Braun 8417s Silver',
#  'price': '27 199 '}
# {'_id': ObjectId('61debc0d519814cbd664beb6'),
#  'image': '//img.mvideo.ru/Pdb/10030108b.jpg',
#  'name': 'Smart Проектор Cinemood CNMD0020E-08WT',
#  'price': '79 999 '}
# {'_id': ObjectId('61debc0d519814cbd664beb7'),
#  'image': '//img.mvideo.ru/Pdb/50167166b.jpg',
#  'name': 'Наушники True Wireless Xiaomi Redmi Buds 3 M2104E1 (BHR5174GL)',
#  'price': '3 499 '}
# {'_id': ObjectId('61debc0d519814cbd664beb8'),
#  'image': '//img.mvideo.ru/Pdb/20078400b.jpg',
#  'name': 'Фен-стайлер Redmond RMS-4305',
#  'price': '2 799 \n3 999 '}
# {'_id': ObjectId('61debc0d519814cbd664beb9'),
#  'image': '//img.mvideo.ru/Pdb/20077034b.jpg',
#  'name': 'Аэрогриль Xiaomi Mi Smart Air Fryer 3.5L BHR4849EU',
#  'price': '7 999 '}
# {'_id': ObjectId('61debc0d519814cbd664beba'),
#  'image': '//img.mvideo.ru/Pdb/20078453b.jpg',
#  'name': 'Кофеварка капсульная Bosch TAS1002N',
#  'price': '4 999 '}
# {'_id': ObjectId('61debc0d519814cbd664bebb'),
#  'image': '//img.mvideo.ru/Pdb/20078491b.jpg',
#  'name': 'Утюг Rowenta DW5325D1',
#  'price': '7 999 \n11 499 '}
# {'_id': ObjectId('61debc0d519814cbd664bebc'),
#  'image': '//img.mvideo.ru/Pdb/20077643b.jpg',
#  'name': 'Стиральная машина узкая Samsung WW80A6S28AN',
#  'price': '47 999 '}
# {'_id': ObjectId('61debc0d519814cbd664bebd'),
#  'image': '//img.mvideo.ru/Pdb/20077659b.jpg',
#  'name': 'Холодильник многодверный Samsung RH62A50F1SL',
#  'price': '119 999 '}
# {'_id': ObjectId('61debc0d519814cbd664bebe'),
#  'image': '//img.mvideo.ru/Pdb/10029752b.jpg',
#  'name': 'Видеорегистратор Mio MiVue C421',
#  'price': '5 299 '}
# {'_id': ObjectId('61debc0d519814cbd664bebf'),
#  'image': '//img.mvideo.ru/Pdb/40077181b.jpg',
#  'name': 'Электронная книга PocketBook 740 Pro Metallic Grey (PB740-2-J-RU)',
#  'price': '19 999 '}
# {'_id': ObjectId('61debc0d519814cbd664bec0'),
#  'set_goods_all_info': '-13%\n'
#                        'Смартфон Xiaomi 11 Lite 5G NE 256GB Peach Pink\n'
#                        'нет отзывов\n'
#                        '34 999 \n'
#                        '39 999 \n'
#                        '+1 050 Бонусных рублей\n'
#                        'Колонка умная Xiaomi Mi Smart Speaker (QBH4221RU)\n'
#                        '5,0\n'
#                        '4 отзыва\n'
#                        '4 999 \n'
#                        '+150 Бонусных рублей\n'
#                        'Ноутбук HUAWEI MateBook D 15 BoD-WDH9 8+512GB Space '
#                        'Grey\n'
#                        'нет отзывов\n'
#                        '63 999 \n'
#                        '+1 920 Бонусных рублей\n'
#                        '-17%\n'
#                        'Подписка M.Prime на 1 месяц + Яндекс.Плюс\n'
#                        'нет отзывов\n'
#                        '499 \n'
#                        '599 \n'
#                        '+15 Бонусных рублей\n'
#                        'Триммер Philips QP2510/11\n'
#                        'нет отзывов\n'
#                        '2 599 \n'
#                        '+78 Бонусных рублей\n'
#                        'Электробритва Braun 8417s Silver\n'
#                        '5,0\n'
#                        '23 отзыва\n'
#                        '27 199 \n'
#                        '+816 Бонусных рублей\n'
#                        'Smart Проектор Cinemood CNMD0020E-08WT\n'
#                        'нет отзывов\n'
#                        '79 999 \n'
#                        '+2 400 Бонусных рублей\n'
#                        'Наушники True Wireless Xiaomi Redmi Buds 3 M2104E1 '
#                        '(BHR5174GL)\n'
#                        '4,0\n'
#                        '5 отзывов\n'
#                        '3 499 \n'
#                        '+105 Бонусных рублей\n'
#                        'Распродажа\n'
#                        '-30%\n'
#                        'Фен-стайлер Redmond RMS-4305\n'
#                        'нет отзывов\n'
#                        '2 799 \n'
#                        '3 999 \n'
#                        '+84 Бонусных рубля\n'
#                        'Аэрогриль Xiaomi Mi Smart Air Fryer 3.5L BHR4849EU\n'
#                        '5,0\n'
#                        '4 отзыва\n'
#                        '7 999 \n'
#                        '+240 Бонусных рублей\n'
#                        'Кофеварка капсульная Bosch TAS1002N\n'
#                        'нет отзывов\n'
#                        '4 999 \n'
#                        '+150 Бонусных рублей\n'
#                        'Мега рассрочка\n'
#                        '-30%\n'
#                        'Утюг Rowenta DW5325D1\n'
#                        'нет отзывов\n'
#                        '7 999 \n'
#                        '11 499 \n'
#                        '+240 Бонусных рублей\n'
#                        'Скидка 10%\n'
#                        'Стиральная машина узкая Samsung WW80A6S28AN\n'
#                        '5,0\n'
#                        '3 отзыва\n'
#                        '47 999 \n'
#                        '+1 440 Бонусных рублей\n'
#                        'Холодильник многодверный Samsung RH62A50F1SL\n'
#                        '5,0\n'
#                        '2 отзыва\n'
#                        '119 999 \n'
#                        '+3 600 Бонусных рублей\n'
#                        'Видеорегистратор Mio MiVue C421\n'
#                        '5,0\n'
#                        '2 отзыва\n'
#                        '5 299 \n'
#                        '+159 Бонусных рублей\n'
#                        'Электронная книга PocketBook 740 Pro Metallic Grey '
#                        '(PB740-2-J-RU)\n'
#                        '5,0\n'
#                        '2 отзыва\n'
#                        '19 999 \n'
#                        '+600 Бонусных рублей'}
