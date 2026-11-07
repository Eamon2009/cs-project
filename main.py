# CLOUD server rental management system -class 12 CBSE CS project
# Theme : business (a comapany rents cloud servers to customers)
# Language : Python3
# Database : MySQL (using it via pymysql)



import pymysql
import datetime

DB_NAME = "cloudrent"
HOST = "localhost"
USER = "root"
PASSWD = "eamon_device=CUDA11092009!@#"

def setup_database():
    con = pymysql.connect(host=HOST, user=USER, password=PASSWD)
    cur = con.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS " + DB_NAME)
    con.close()
    con = pymysql.connect(host=HOST, user=USER, password=PASSWD, database=DB_NAME)
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS servers(
                      server_id INT PRIMARY KEY AUTO_INCREMENT,
                      plan_name VARCHAR(50) NOT NULL,
                      specs VARCHAR(100) NOT NULL,
                      daily_rate FLOAT NOT NULL,
                      total_units INT DEFAULT 1,
                      available_units INT DEFAULT 1)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS rentals(
                      rental_id INT PRIMARY KEY AUTO_INCREMENT,
                      server_id INT,
                      customer_name VARCHAR(50) NOT NULL,
                      rent_date DATE NOT NULL,
                      release_date DATE,
                      days_used INT,
                      bill_amount FLOAT,
                      FOREIGN KEY (server_id) REFERENCES servers(server_id))""")

    con.commit()
    return con
con = setup_database()
cur = con.cursor()

def show_servers(rows):
    print(f"{'ID':<5}{'Plan':<15}{'Specs':<32}{'Rate/day':<10}{'Avail':<7}{'Total'}")
    print("-" * 78)
    for r in rows:
        # r = (server_id, plan_name, specs, daily_rate, available_units, total_units)
        print(f"{r[0]:<5}{r[1]:<15}{r[2]:<32}{r[3]:<10}{r[4]:<7}{r[5]}")

def add_server():
    name = input("Enter plan name (e.g. VPS-Basic): ")
    specs = input("Enter specs (e.g. 2 CPU / 4 GB RAM / 50 GB SSD): ")
    try:
        rate = float(input("Enter daily rental rate (Rs.): "))
        units = int(input("Enter number of units available: "))
    except ValueError:
        print("Invalid number. Rate set to 100, units set to 1.")
        rate = 100.0
        units = 1

    cur.execute("""INSERT INTO servers(plan_name, specs, daily_rate, total_units, available_units)
                   VALUES(%s, %s, %s, %s, %s)""", (name, specs, rate, units, units))
    con.commit()
    print("Server plan added successfully.")

def rent_server():
    server_id = input("Enter Server ID to rent: ")
    customer = input("Enter customer name: ")
    try:
        days = int(input("Enter number of days to rent: "))
    except ValueError:
        print("Days must be a number.")
        return

    cur.execute("SELECT available_units, daily_rate, plan_name FROM servers WHERE server_id = %s",
                (server_id,))
    row = cur.fetchone()

    if row is None:
        print("Server plan not found.")
        return
    if row[0] == 0:
        print("No units available right now.")
        return
    if days <= 0:
        print("Days must be greater than zero.")
        return

    available, rate, plan = row
    today = datetime.date.today()

    cur.execute("INSERT INTO rentals(server_id, customer_name, rent_date) VALUES(%s, %s, %s)",
                (server_id, customer, today))
    cur.execute("UPDATE servers SET available_units = available_units - 1 WHERE server_id = %s",
                (server_id,))
    con.commit()

    estimate = rate * days          # rate x days
    print(f"{plan} rented to {customer} on {today}")
    print(f"  Estimated bill for {days} day(s): Rs. {estimate:.2f}")


def release_server():
    try:
        rental_id = int(input("Enter Rental ID: "))
    except ValueError:
        print("Rental ID must be a number.")
        return

    cur.execute("""SELECT rentals.server_id, rentals.rent_date, servers.daily_rate
                   FROM rentals JOIN servers ON rentals.server_id = servers.server_id
                   WHERE rentals.rental_id = %s AND rentals.release_date IS NULL""",
                (rental_id,))
    row = cur.fetchone()

    if row is None:
        print("Rental not found or already released.")
        return

    server_id, rent_date, rate = row
    today = datetime.date.today()

    days_used = (today - rent_date).days     
    if days_used == 0:
        days_used = 1                        # minimum 1 day charge
    bill = days_used * rate                  # bill = days x rate

    cur.execute("""UPDATE rentals SET release_date = %s, days_used = %s, bill_amount = %s
                   WHERE rental_id = %s""", (today, days_used, bill, rental_id))
    cur.execute("UPDATE servers SET available_units = available_units + 1 WHERE server_id = %s",
                (server_id,))
    con.commit()

    print(f"Server released on {today}")
    print(f"  Days used: {days_used}   Total bill: Rs. {bill:.2f}")


def search_servers():
    keyword = input("Enter plan name or specs to search: ")
    like = "%" + keyword + "%"
    cur.execute("""SELECT server_id, plan_name, specs, daily_rate, available_units, total_units
                   FROM servers WHERE plan_name LIKE %s OR specs LIKE %s""", (like, like))
    rows = cur.fetchall()

    if rows:
        show_servers(rows)
    else:
        print("No matching server plans found.")

def view_servers():
    cur.execute("""SELECT server_id, plan_name, specs, daily_rate, available_units, total_units
                   FROM servers""")
    rows = cur.fetchall()

    if rows:
        show_servers(rows)
    else:
        print("No server plans yet. Add some first.")
def view_rentals():
    cur.execute("""SELECT rentals.rental_id, servers.plan_name, rentals.customer_name,
                          rentals.rent_date, rentals.release_date,
                          rentals.days_used, rentals.bill_amount
                   FROM rentals JOIN servers ON rentals.server_id = servers.server_id""")
    rows = cur.fetchall()

    if not rows:
        print("No rentals yet.")
        return

    print(f"{'ID':<4}{'Plan':<13}{'Customer':<16}{'Rented':<12}{'Released':<12}{'Days':<6}{'Bill'}")
    print("-" * 72)

    revenue = 0
    for r in rows:
        rental_id, plan, customer, rent_date, release_date, days, bill = r

        if release_date:
            released = str(release_date)
        else:
            released = "Active"          # empty = still rented

        if bill:
            bill_text = f"Rs.{bill:.0f}"
            revenue = revenue + bill
        else:
            bill_text = "-"

        if days:
            days_text = str(days)
        else:
            days_text = "-"

        print(f"{rental_id:<4}{plan:<13}{customer:<16}{str(rent_date):<12}"
              f"{released:<12}{days_text:<6}{bill_text}")

    print("-" * 72)
    print(f"TOTAL REVENUE EARNED: Rs. {revenue:.2f}")


def menu():
    while True:
        print("WELCOME TO CLOUD SERVERS !!!")
        print("1. Add Server Plan")
        print("2. Rent a Server")
        print("3. Release a Server (with Bill)")
        print("4. Search Server Plans")
        print("5. View All Servers")
        print("6. View Rentals & Revenue")
        print("7. Exit")
        choice = input("Enter your choice (1-7): ")

        if choice == "1":
            add_server()
        elif choice == "2":
            rent_server()
        elif choice == "3":
            release_server()
        elif choice == "4":
            search_servers()
        elif choice == "5":
            view_servers()
        elif choice == "6":
            view_rentals()
        elif choice == "7":
            print("Thank you for using Cloud Rental Manager!")
            con.close()
            break
        else:
            print("Invalid choice. Please try again.")

menu()
