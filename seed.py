from datetime import date

from app.database import Base, SessionLocal, engine
from app.models import Customer, Order, Payment


def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if db.query(Customer).first():
            print("Database already contains data.")
            return

        customers = [
            Customer(name="Rahul", email="rahul@example.com", signup_date=date(2026, 8, 5)),
            Customer(name="Priya", email="priya@example.com", signup_date=date(2026, 8, 12)),
            Customer(name="Aman", email="aman@example.com", signup_date=date(2026, 7, 15)),
        ]
        db.add_all(customers)
        db.flush()

        db.add_all([
            Order(customer_id=customers[0].id, amount=5000, order_date=date(2026, 8, 10)),
            Order(customer_id=customers[0].id, amount=3000, order_date=date(2026, 8, 20)),
            Order(customer_id=customers[1].id, amount=12000, order_date=date(2026, 8, 15)),
            Order(customer_id=customers[2].id, amount=2000, order_date=date(2026, 8, 2)),
            Payment(customer_id=customers[0].id, amount=8000, payment_date=date(2026, 8, 21)),
            Payment(customer_id=customers[1].id, amount=12000, payment_date=date(2026, 8, 16)),
        ])

        db.commit()
        print("Database seeded successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
