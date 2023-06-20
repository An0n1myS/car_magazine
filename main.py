import secrets
import base64
from datetime import datetime, date

from flask import Flask, render_template, request, redirect, session, url_for, flash

import pymysql

app = Flask(__name__, template_folder="./")

app.secret_key = secrets.token_hex(16)

# Параметри підключення до бази даних
db_host = 'localhost'
db_user = 'root'
db_password = ''
db_name = 'autoshop_db'


# Функція для встановлення підключення до бази даних
def connect_to_database():
    return pymysql.connect(host=db_host, user=db_user, password=db_password, database=db_name)

# функция для проверки, авторизован ли пользователь
def is_logged_in():
    return 'username' in session

# Головна сторінка
@app.route('/')
def home():
    # Отримати список товарів з бази даних
    connection = connect_to_database()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM parts")
    products_data = cursor.fetchall()

    products = []
    for product in products_data:
        part_id = product[0]
        name = product[1]
        price = product[2]
        description = product[3]
        quantity = product[4]
        category_id = product[5]
        manufacturer_id = product[6]
        created_at = product[7]


        encoded_photo = base64.b64encode(product[5]).decode('utf-8')


        product_data = {
            'part_id': part_id,
            'name': name,
            'price': price,
            'description': description,
            'quantity': quantity,
            'category_id': category_id,
            'manufacturer_id': manufacturer_id,
            'created_at': created_at,
            'photos': encoded_photo
        }

        products.append(product_data)

    # Отримати список категорій з бази даних
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()

    # Отримати список виробників з бази даних
    cursor.execute("SELECT * FROM manufacturers")
    manufacturers = cursor.fetchall()

    connection.close()

    return render_template('index.html', products=products, categories=categories, manufacturers=manufacturers)

# Сторінка категорії
@app.route('/category')
def category():
    # Отримати дані категорії з бази даних
    connection = connect_to_database()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM categories")
    category_data = cursor.fetchone()

    return render_template('pages/category.html', category=category_data)
# Сторінка категорії
@app.route('/category/<int:category_id>')
def category_id(category_id):
    # Отримати дані категорії з бази даних
    connection = connect_to_database()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM categories WHERE category_id = %s", (category_id,))
    category_data = cursor.fetchone()

    # Отримати список запчастин для даної категорії
    cursor.execute("SELECT * FROM parts WHERE category_id = %s", (category_id,))
    parts = cursor.fetchall()
    connection.close()

    return render_template('pages/category_parts.html', category=category_data, parts=parts)


# Сторінка деталі запчастини
@app.route('/part/<int:part_id>')
def part(part_id):
    # Отримати список товарів з бази даних
    connection = connect_to_database()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM parts WHERE part_id = %s", (part_id,))
    product = cursor.fetchone()

    encoded_photo = base64.b64encode(product[5]).decode('utf-8')

    product_data = {
        'part_id': product[0],
        'name': product[1],
        'price': product[2],
        'description': product[3],
        'quantity': product[4],
        'category_id': product[5],
        'manufacturer_id': product[6],
        'created_at': product[7],
        'photos': encoded_photo
    }

    cursor.execute("SELECT * FROM comments WHERE part_id = %s", (part_id,))
    comments_data = cursor.fetchall()


    comments = []
    for comment_data in comments_data:
        cursor.execute("SELECT * FROM clients WHERE client_id = %s", (comment_data[2],))
        client = cursor.fetchone()
        info_client = client[1] + ' ' + client[2]
        comment = {
            'comment_id': comment_data[0],
            'part_id': comment_data[1],
            'client': info_client,
            'text': comment_data[3],
            'rating': comment_data[4],
            'comment_date': comment_data[5]
        }
        comments.append(comment)

    # Отримати рейтинг товару
    cursor.execute("SELECT AVG(rating) FROM comments WHERE part_id = %s", (part_id,))
    average_rating = cursor.fetchone()[0]

    connection.close()

    return render_template('pages/parts.html', part=product_data, comments=comments, average_rating=average_rating)


# Обробник форми авторизації
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Перевірка авторизаційних даних в базі даних
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM clients WHERE email = %s AND password = %s", (email, password))
        client = cursor.fetchone()
        connection.close()

        if client:
            # Збереження ідентифікатора клієнта у сеансі
            session['username'] = client[0]
            return redirect('/')
        else:
            error_message = "Невірний email або пароль"
            return render_template('templates/login.html', error=error_message)

    return render_template('templates/login.html')


# Обробник форми реєстрації
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        # Збереження даних клієнта в базі даних
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO clients (first_name, last_name, email,phone, password) VALUES (%s, %s, %s, %s, %s)",
                       (first_name, last_name, email,phone, password))
        connection.commit()
        connection.close()

        # Перенаправлення на сторінку авторизації
        return redirect('/login')

    return render_template('templates/register.html')



# Обробник виходу
@app.route('/logout')
def logout():
    # Видалення ідентифікатора клієнта з сеансу
    session.pop('username', None)
    return redirect('/')


# Маршрут для сторінки профілю
@app.route('/profile')
def profile():
    if 'username' in session:
        connection = connect_to_database()

        # Отримання даних про користувача з бази даних
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM clients WHERE client_id = %s", (session['username'],))
            user_query = cursor.fetchone()

            user = {
                'first_name': user_query[1],
                'last_name': user_query[2],
                'email': user_query[3],
                'phone': user_query[4],
                'created_at': user_query[6]
            }

            # Отримання даних про замовлення користувача з бази даних
            cursor.execute("SELECT * FROM orders WHERE client_id = %s", (session['username'],))
            orders_query = cursor.fetchall()

            orders = []
            for order_query in orders_query:
                order = {
                    'order_id': order_query[0],
                    'order_date': order_query[1],
                    'status': order_query[2]
                }
                orders.append(order)

        return render_template('pages/profile.html', user=user, orders=orders)

    elif 'username' not in session:
        return redirect('/login')


# Маршрут для сторінки кошика
@app.route('/cart')
def cart():
    if 'username' in session:
        connection = connect_to_database()
        # Отримання вмісту кошика користувача з бази даних
        with connection.cursor() as cursor:
            cursor.execute("SELECT parts.name, parts.price, cart.count FROM parts JOIN cart ON parts.part_id = cart.part_id JOIN clients ON cart.client_id = clients.client_id WHERE clients.client_id = %s", (session['username'],))
            cart_items_query = cursor.fetchall()
            cart_items = []
            for item in cart_items_query:
                cart_items.append({'name': item[0], 'price': item[1], 'count': item[2]})
        return render_template('pages/cart.html', cart_items=cart_items)
    else:
        return redirect('/login')


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    part_id = request.form['part_id']
    client_id = session['username']
    count = request.form['count']

    connection = connect_to_database()
    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO cart (part_id, client_id, count) VALUES (%s, %s, %s)",
                       (part_id, client_id, count))
        connection.commit()

    flash('Товар успішно доданий до кошика!', 'success')
    return redirect('/cart')

@app.route('/add_comment', methods=['POST'])
def add_comment():
    connection = connect_to_database()

    part_id = request.form['comment_part_id']
    client_id = session['username']
    text = request.form['comment-text']
    rating = request.form['comment_rating']
    comment_date = date.today()

    with connection.cursor() as cursor:
        # Вставка коментаря в базу даних
        cursor.execute(
            "INSERT INTO comments (part_id, client_id, text, rating, comment_date) VALUES (%s, %s, %s, %s, %s)",
            (part_id, client_id, text, rating, comment_date))
        connection.commit()

    return redirect('/part/' + part_id)


# Маршрут для сторінки створення замовлення
@app.route('/create_order', methods=['GET', 'POST'])
def create_order():
    if request.method == 'POST':
        connection = connect_to_database()
        # Отримання даних форми замовлення
        # Збереження замовлення в базі даних
        with connection.cursor() as cursor:
            order_date = datetime.now().date()
            status = 'В процесі'
            cursor.execute("INSERT INTO orders (order_date, status, client_id) VALUES (%s, %s, %s)", (order_date, status, session['username']))
            order_id = cursor.lastrowid

            # Отримання вмісту кошика користувача
            cursor.execute("SELECT * FROM cart WHERE client_id = %s", (session['username'],))
            cart_items = cursor.fetchall()

            # Додавання деталей замовлення
            for item in cart_items:
                cursor.execute("INSERT INTO order_details (order_id, part_id, quantity) VALUES (%s, %s, %s)", (order_id, item[0], item[1]))


            # Видалення вмісту кошика
            cursor.execute("DELETE FROM cart WHERE client_id = %s", (session['username'],))

        connection.commit()
        return redirect(url_for('order_confirmation'))
    return render_template('pages/order_confirmation.html')

# Маршрут для сторінки підтвердження замовлення
@app.route('/order_confirmation')
def order_confirmation():
    connection = connect_to_database()
    # Отримання даних підтвердження замовлення з бази даних
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM orders WHERE client_id = %s ORDER BY order_id DESC LIMIT 1", (session['username'],))
        order_result = cursor.fetchone()

        if order_result:
            order_fields = [field[0] for field in cursor.description]
            order = dict(zip(order_fields, order_result))

            cursor.execute("SELECT parts.name, parts.price, order_details.quantity FROM parts JOIN order_details ON parts.part_id = order_details.part_id WHERE order_details.order_id = %s", (order['order_id'],))
            order_details_result = cursor.fetchall()

            order_details_fields = [field[0] for field in cursor.description]
            order_details = [dict(zip(order_details_fields, row)) for row in order_details_result]
        else:
            order = None
            order_details = []

    return render_template('pages/order_confirmation.html', order=order, order_details=order_details)


# Маршрут для сторінки оплати
@app.route('/payment')
def payment():
    connection = connect_to_database()
    # Отримання даних замовлення для оплати з бази даних
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM orders WHERE client_id = %s ORDER BY order_id DESC LIMIT 1", (session['username'],))
        order = cursor.fetchone()
    return render_template('pages/payment.html', order=order)

if __name__ == '__main__':
    app.run(debug=True)
