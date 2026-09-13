from datetime import date

from app.database import Base, SessionLocal, engine
from app.models import Customer, Engagement, Order, Payment


def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if db.query(Customer).first():
            print("Database already contains data. Delete company.db and run seed.py to rebuild it.")
            return

        customers = [
            Customer(name="Rahul", email="rahul@example.com", signup_date=date(2026, 8, 5)),
            Customer(name="Priya", email="priya@example.com", signup_date=date(2026, 8, 12)),
            Customer(name="Aman", email="aman@example.com", signup_date=date(2026, 7, 15)),
            Customer(name="Neha", email="neha@example.com", signup_date=date(2026, 8, 18)),
        ]
        db.add_all(customers)
        db.flush()

        db.add_all([
            Order(customer_id=customers[0].id, amount=5000, order_date=date(2026, 8, 10)),
            Order(customer_id=customers[0].id, amount=3000, order_date=date(2026, 8, 20)),
            Order(customer_id=customers[1].id, amount=12000, order_date=date(2026, 8, 15)),
            Order(customer_id=customers[2].id, amount=2000, order_date=date(2026, 8, 2)),
            Order(customer_id=customers[3].id, amount=2500, order_date=date(2026, 8, 22)),
            Order(customer_id=customers[3].id, amount=1800, order_date=date(2026, 8, 25)),
            Order(customer_id=customers[3].id, amount=1500, order_date=date(2026, 8, 29)),
            Payment(customer_id=customers[0].id, amount=8000, payment_date=date(2026, 8, 21)),
            Payment(customer_id=customers[1].id, amount=12000, payment_date=date(2026, 8, 16)),
            Payment(customer_id=customers[3].id, amount=5800, payment_date=date(2026, 8, 30)),
            Engagement(customer_id=customers[0].id, channel="email", campaign="August Offers", responded=True, engagement_date=date(2026, 8, 11)),
            Engagement(customer_id=customers[0].id, channel="email", campaign="Weekend Sale", responded=False, engagement_date=date(2026, 8, 19)),
            Engagement(customer_id=customers[1].id, channel="email", campaign="August Offers", responded=True, engagement_date=date(2026, 8, 14)),
            Engagement(customer_id=customers[2].id, channel="email", campaign="August Offers", responded=False, engagement_date=date(2026, 8, 6)),
            Engagement(customer_id=customers[3].id, channel="email", campaign="August Offers", responded=True, engagement_date=date(2026, 8, 20)),
            Engagement(customer_id=customers[3].id, channel="email", campaign="Weekend Sale", responded=True, engagement_date=date(2026, 8, 24)),
            Engagement(customer_id=customers[3].id, channel="email", campaign="Month End Offer", responded=True, engagement_date=date(2026, 8, 28)),
        ])

        db.commit()
        print("Database seeded successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
