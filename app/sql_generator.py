def generate_sql(question: str, clarification: str | None = None) -> str | None:
    normalized = question.lower().strip()

    if "best customer" in normalized or "top customer" in normalized:
        if clarification == "Highest revenue":
            return """
            SELECT c.name, SUM(o.amount) AS total_revenue
            FROM customers c
            JOIN orders o ON c.id = o.customer_id
            GROUP BY c.id, c.name
            ORDER BY total_revenue DESC
            LIMIT 1;
            """

        if clarification == "Highest number of orders":
            return """
            SELECT c.name, COUNT(o.id) AS total_orders
            FROM customers c
            JOIN orders o ON c.id = o.customer_id
            GROUP BY c.id, c.name
            ORDER BY total_orders DESC
            LIMIT 1;
            """

    if "how many customers" in normalized or "total customers" in normalized:
        return "SELECT COUNT(*) AS total_customers FROM customers;"

    return None
