from flask import Flask, render_template, request
import mysql.connector
import requests
from dotenv import load_dotenv
import os


app = Flask(__name__)

# Load environment variables from the .env file
load_dotenv()

# Access the variables
db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

# MySQL database connection
def get_db_connection():
    conn = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    return conn

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    conversion_rate = None  # Initialize conversion_rate
    if request.method == 'POST':
        base_currency = request.form['base_currency']
        target_currency = request.form['target_currency']
        amount = float(request.form['amount'])

        connection = get_db_connection()
        cursor = connection.cursor()

        # Retrieve exchange rate from MySQL
        query = """
        SELECT rate FROM exchange_rates 
        WHERE base_currency = %s AND target_currency = %s
        """
        cursor.execute(query, (base_currency, target_currency,))
        row = cursor.fetchone()

        if row:
            conversion_rate = float(row[0])
        else:
            # Fetch from external API if not found in MySQL
            api_url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
            response = requests.get(api_url)
            data = response.json()

            if target_currency in data['rates']:
                conversion_rate = data['rates'][target_currency]

                # Save to MySQL
                insert_query = """
                INSERT INTO exchange_rates (base_currency, target_currency, rate) 
                VALUES (%s, %s, %s) 
                ON DUPLICATE KEY UPDATE rate = VALUES(rate)
                """
                cursor.execute(insert_query, (base_currency, target_currency, conversion_rate))
                connection.commit()
            else:
                conversion_rate = None

        if conversion_rate:
            result = amount * conversion_rate

        cursor.close()
        connection.close()

    return render_template('index.html', result=result,conversion_rate=conversion_rate)

if __name__ == '__main__':
    app.run(debug=True)
