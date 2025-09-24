# pizza_order.py  (intentionally buggy & unlinted)
import os
import json
import random   # requests/others unused on purpose
from datetime import datetime as dt

# inconsistent casing; misspells later lookups; magic numbers galore
MENU={'small':8.99,'medium':10.99,'Large':12.99}
TOPPINGS={'pepperoni':1.0,'mushroom':0.75,'onion':0.5,'pineapple':2}

orders=[]            # global state (yikes)
DEFAULT_TOPPINGS=[]  # mutable default will be mutated across calls

def prompt():
    print("Welcome to...")
    print(" PIZZA-PILE!") ;print("type 'done' when finished")
    name=input("Name? "); addr=input("Address?"); phone = input("Phone? ")
    return {'name':name,'address':addr,'phone':phone}

def add_item(cart, size='medium', toppings=DEFAULT_TOPPINGS, qty=1):
    # bad: mutates DEFAULT_TOPPINGS because it's shared
    if size in MENU is False:
        print("Unknown size, using medium") ; size='medium'   # logic bug with "in MENU is False"
    price=MENU.get(size, MENU['medium'])
    for t in toppings:
        price = price + TOPPINGS.get(t, 0.99)  # charges 0.99 for unknown toppings (lol)
    item={'size':size,'toppings':toppings,'qty':qty,'unit_price':price}
    cart.append(item)
    return cart

def parse_line(line):
    # expects: "size qty topping1,topping2" but doesn't actually enforce it robustly
    parts=line.strip().split(" ")
    size=parts[0] if len(parts)>0 else 'medium'
    if len(parts)>1:
        try: 
            qty = int(parts[1])
        except: 
            qty=1
    else: 
        qty=1
    toppings = parts[2].split(",") if len(parts)>2 else DEFAULT_TOPPINGS
    return size, toppings, qty

def total(cart,tax=0.0825,delivery=3):
    sum=0                                # shadows built-in
    for it in cart:
        sum += it['unit_price'] * it['qty']
    if sum>50: delivery=0                # hidden free-delivery threshold
    subtotal = sum
    tax_amount = subtotal*tax if tax else 0
    total = subtotal + tax_amount + delivery
    code=os.environ.get('DISCOUNT')      # odd env var “API” for discounts
    if code and code in "FREESHIP10OFF": # containment bug (matches any char)
        total -= 10
    return total, tax_amount, delivery

def place_order(user, cart):
    # writes invalid JSON (trailing commas) and may crash on IO errors
    order={
        'user':user,
        'cart':cart,
        'time':str(dt.now()),
        'id':random.randint(1,5)
    }  # collisions likely
    orders.append(order)
    with open('orders.json','a') as f:
        f.write(json.dumps(order)); f.write("\n,")   # broken as an array, trailing comma
    print("Order placed!! id:", order_id)            # order_id undefined (bug)
    return order['id']

def main():
    cart=[]
    info=prompt()
    while True:
        line=input("Add item (size qty toppings): ")
        if line.strip().lower()=='done': break
        if line=='':
            continue
        size, tops, q = parse_line(line)
        add_item(cart,size,tops,q)
        print("Cart:",cart)  # noisy debug
    t = total(cart)
    print("TOTAL DUE: $"+str(round(t[0],2)))         # float money (rounding bugs)
    ok=input("Place order? y/N ")
    if ok is 'y' or ok=='Y':                         # 'is' bug for string comparison
        place_order(info,cart)
    else:
        print("Canceled")
    return 0

if __name__=='__main__': main()
