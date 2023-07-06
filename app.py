from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
import json
from bson import json_util
from dotenv import load_dotenv
import os
# Get the value of a specific environment variable
load_dotenv()
value = os.getenv('mongo_atlas')
app=Flask(__name__)

# mongodb connection
app.config["MONGO_URI"] = value
db = PyMongo(app).db

# Flask routes
# Fetch all data from MongoDB


@app.route("/", methods=["GET"])
def all_data():
    data = {
        'orders': list(db.orders.find()),
        'menu': list(db.menu.find())
    }
    return json.loads(json_util.dumps(data))


# Add a new dish to the menu
@app.route('/menu', methods=['POST'])
def add_dish_to_menu():
    # Get the dish details from the request body
    dish = request.json
    dish_id=dish["dish_id"]
    dish_name = dish['dish_name']
    price = dish['price']
    availability = dish['availability']

    # Check if the dish already exists in the menu
    if db.menu.find_one({'dish_name': dish_name}):
        return jsonify({'error': f'Dish "{dish_name}" already exists in the menu'}), 400

    # Insert the dish into the menu collection
    db.menu.insert_one({
        'dish_id':dish_id,
        'dish_name': dish_name,
        'price': price,
        'availability': availability
    })

    return jsonify({'message': 'Dish added to the menu successfully'})


# Get the menu
@app.route('/menu', methods=['GET'])
def get_menu():
    menu = list(db.menu.find())
    return json.loads(json_util.dumps(menu))


# Update the availability of a menu item
@app.route('/menu/<int:dish_id>', methods=['PUT'])
def toggle_menu_item_availability(dish_id):
    # Check if the dish ID exists
    dish = db.menu.find_one({'dish_id': dish_id})
    if dish:
        availability = dish['availability']
        new_availability = not availability

        # Update the availability in the menu collection
        db.menu.update_one({'dish_id': dish_id}, {'$set': {'availability': new_availability}})

        return jsonify({'message': 'Menu item availability updated successfully'})
    else:
        return jsonify({'error': f'Dish with ID {dish_id} not found'}), 404




# Delete a dish from the menu
@app.route('/menu/<int:dish_id>', methods=['DELETE'])
def delete_dish_from_menu(dish_id):
    # Check if the dish ID exists
    if db.menu.find_one({'dish_id': dish_id}):
        # Remove the dish from the menu collection
        db.menu.delete_one({'dish_id': dish_id})

        return jsonify({'message': f'Dish with ID {dish_id} deleted from the menu'})
    else:
        return jsonify({'error': f'Dish with ID {dish_id} not found'}), 404


# Update the status of an order
@app.route('/orders/<int:order_id>', methods=['PUT'])
def update_order_status(order_id):
    # Check if the order ID exists
    if db.orders.find_one({'order_id': order_id}):
        data = request.json
        status = data.get('status')
        if status in ['received', 'preparing', 'ready for pickup', 'delivered']:
            # Update the order status in the orders collection
            db.orders.update_one({'order_id': order_id}, {'$set': {'status': status}})

            return jsonify({'message': 'Order status updated successfully'})
        else:
            return jsonify({'message': 'Invalid status'}), 400
    else:
        return jsonify({'message': 'Order not found'}), 404


# Create a new order
@app.route('/orders', methods=['POST'])
def create_order():
    # Get the order details from the request body
    order = request.json
    customer_name = order['customer_name']
    dish_ids = order['dish_ids']
    # Check if all the dishes are available
    for dish_id in dish_ids:
        print(db.menu.find_one({'dish_id': int(dish_id)}))
        if not db.menu.find_one({'dish_id':dish_id}):
            return jsonify({'error': f'Dish with ID {dish_id} is not available'}),400

    # Generate a unique order ID
    order_id = db.orders.count_documents({}) + 1

    # Create the order
    db.orders.insert_one({
        'order_id': order_id,
        'customer_name': customer_name,
        'dish_ids': dish_ids,
        'status': 'received'
    })

    return jsonify({'message': f'Order {order_id} created successfully'})

# Retrieve all orders
@app.route('/orders', methods=['GET'])
def get_orders():
    orders = list(db.orders.find({}, {'_id': 0}))
    return jsonify(orders)


# Get the details of a specific order
@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    # Check if the order ID exists
    order = db.orders.find_one({'order_id': order_id})
    if order:
        return jsonify(order)
    else:
        return jsonify({'error': f'Order {order_id} not found'}), 404


if __name__ == '__main__':
    app.run(debug=True)