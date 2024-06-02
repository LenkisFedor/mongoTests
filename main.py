from datetime import datetime

from pymongo import MongoClient
from bson.objectid import ObjectId
import pytest

# Подключение к базе данных
client = MongoClient('mongodb://localhost:27017/')
db = client['photo_aggr']
orders_collection = db['orders']
services_collection = db['services']
clients_collection = db['clients']
requests_collection = db['requests']


# Функционал поиска заказа

def get_next_sequence_value(collection_name):
    # Получаем максимальное значение _id в указанной коллекции
    max_id = db[collection_name].find_one({}, sort=[('_id', -1)])['_id']
    # Увеличиваем его на единицу
    return max_id + 1 if max_id is not None else 1


def find_service(category=None, keywords=None, min_price=None, max_price=None):
    query = {}
    if category:
        query['service_type'] = category
    if keywords:
        query['$or'] = [
            {'description': {'$regex': keywords, '$options': 'i'}},
            {'service_type': {'$regex': keywords, '$options': 'i'}}
        ]
    if min_price is not None or max_price is not None:
        price_filter = {}
        if min_price is not None:
            price_filter['$gte'] = min_price
        if max_price is not None:
            price_filter['$lte'] = max_price
        query['price'] = price_filter

    return services_collection.find(query)


# Функционал добавления услуг в корзину и подсчета общей стоимости заказа
def create_cart(services):
    cart_services = []
    total_price = 0

    for service in services:
        total_price += int(service['price'])
        cart_services.append(service)

    return total_price, cart_services


def add_requests(client_id, services_cursor):
    today = datetime.today().strftime('%Y-%m-%d')
    client = clients_collection.find_one({'_id': client_id})
    if not client:
        print("Client not found")
        return

    # Создаем новый курсор на основе полученного курсора
    services = list(services_cursor)
    print("Number of services:", len(services))
    print("Services list:", services)

    for service in services:
        request = {
            '_id': get_next_sequence_value('requests'),
            'client_id': client_id,
            'date_requested': today,
            'type': service['service_type'],
            'location': client['location']
        }
        requests_collection.insert_one(request)
        print(f"Request added for service {service['_id']}")


print("Поиск по категории")
for service in find_service(category="портрет"):
    print(service)
print()

print("Поиск по ключевым словам")
for service in find_service(keywords="съемке"):
    print(service)
print()

print("Поиск с фильтром по цене меньше 9 000")
for service in find_service(max_price=9000):
    print(service)
print()

print("Поиск с фильтром по цене больше 20 000")
for service in find_service(min_price=20000):
    print(service)
print()

print("Добавление всех услуг прошедших сортировку по цене в корзину")

print(create_cart(find_service(min_price=20000))[0])

services_cursor = find_service(min_price=20000)
services_list = list(services_cursor)

add_requests(1, create_cart(find_service(min_price=20000))[1])

print(find_service(min_price=20000))

for service in find_service(min_price=20000):
    print(service)