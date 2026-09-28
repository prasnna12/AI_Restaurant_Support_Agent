"""Seed the database with sample data for demonstration."""
import json
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.core.config import settings
from app.models.models import (
    AdminUser, Customer, Order, OrderItem, SupportTicket,
    TicketTimeline, KnowledgeDocument, Conversation, ConversationMessage
)


def utcnow():
    return datetime.now(timezone.utc)


SAMPLE_CUSTOMERS = [
    {"name": "Alice Johnson", "email": "alice@example.com", "phone": "+1-555-0101", "address": "123 Oak Street, Springfield"},
    {"name": "Bob Martinez", "email": "bob@example.com", "phone": "+1-555-0102", "address": "456 Pine Ave, Shelbyville"},
    {"name": "Carol Smith", "email": "carol@example.com", "phone": "+1-555-0103", "address": "789 Maple Rd, Capital City"},
    {"name": "David Lee", "email": "david@example.com", "phone": "+1-555-0104", "address": "321 Elm St, Ogdenville"},
    {"name": "Emma Davis", "email": "emma@example.com", "phone": "+1-555-0105", "address": "654 Birch Blvd, North Haverbrook"},
]

SAMPLE_ORDERS = [
    {
        "order_id": "ORD-1001",
        "customer_idx": 0,
        "status": "delivered",
        "items": [
            {"name": "Margherita Pizza", "quantity": 2, "unit_price": 12.99},
            {"name": "Garlic Bread", "quantity": 1, "unit_price": 4.50},
            {"name": "Coke 330ml", "quantity": 2, "unit_price": 2.50},
        ],
        "notes": "Extra cheese on pizza",
        "days_ago": 5,
    },
    {
        "order_id": "ORD-1002",
        "customer_idx": 1,
        "status": "preparing",
        "items": [
            {"name": "Chicken Burger", "quantity": 1, "unit_price": 9.99},
            {"name": "French Fries (Large)", "quantity": 1, "unit_price": 4.99},
            {"name": "Milkshake", "quantity": 1, "unit_price": 5.99},
        ],
        "notes": "",
        "days_ago": 0,
    },
    {
        "order_id": "ORD-1003",
        "customer_idx": 2,
        "status": "out_for_delivery",
        "items": [
            {"name": "Veggie Wrap", "quantity": 2, "unit_price": 8.50},
            {"name": "Side Salad", "quantity": 2, "unit_price": 3.50},
            {"name": "Sparkling Water", "quantity": 3, "unit_price": 1.99},
        ],
        "notes": "Deliver to side entrance",
        "days_ago": 0,
    },
    {
        "order_id": "ORD-1004",
        "customer_idx": 3,
        "status": "cancelled",
        "items": [
            {"name": "Pasta Carbonara", "quantity": 1, "unit_price": 13.99},
        ],
        "notes": "Customer cancelled",
        "days_ago": 2,
    },
    {
        "order_id": "ORD-1005",
        "customer_idx": 4,
        "status": "failed",
        "items": [
            {"name": "BBQ Ribs", "quantity": 1, "unit_price": 18.99},
            {"name": "Coleslaw", "quantity": 1, "unit_price": 3.50},
            {"name": "Beer 500ml", "quantity": 2, "unit_price": 5.50},
        ],
        "notes": "Payment failed but deducted",
        "days_ago": 1,
    },
    {
        "order_id": "ORD-1006",
        "customer_idx": 0,
        "status": "pending",
        "items": [
            {"name": "Sushi Platter (8 pcs)", "quantity": 1, "unit_price": 16.99},
            {"name": "Miso Soup", "quantity": 2, "unit_price": 2.50},
        ],
        "notes": "",
        "days_ago": 0,
    },
    {
        "order_id": "ORD-1007",
        "customer_idx": 1,
        "status": "confirmed",
        "items": [
            {"name": "Pepperoni Pizza", "quantity": 1, "unit_price": 14.99},
            {"name": "Wings (6 pcs)", "quantity": 1, "unit_price": 8.99},
        ],
        "notes": "",
        "days_ago": 0,
    },
]

SAMPLE_TICKETS = [
    {
        "ticket_id": "TKT-0001",
        "customer_idx": 4,
        "order_id": "ORD-1005",
        "title": "Payment deducted but order failed",
        "description": "My payment of $33.49 was deducted from my card but the order shows as failed. I need a refund urgently.",
        "category": "Payment",
        "priority": "High",
        "status": "Open",
        "assigned_team": "Payments Team",
        "idempotency_key": "auto-ORD-1005-payment-failed",
    },
    {
        "ticket_id": "TKT-0002",
        "customer_idx": 3,
        "order_id": "ORD-1004",
        "title": "Request refund for cancelled order",
        "description": "I cancelled my order ORD-1004 but have not received my refund yet.",
        "category": "Refund",
        "priority": "Medium",
        "status": "In Progress",
        "assigned_team": "Refund Team",
        "idempotency_key": "auto-ORD-1004-refund-request",
    },
    {
        "ticket_id": "TKT-0003",
        "customer_idx": 2,
        "order_id": "ORD-1003",
        "title": "Order taking too long to deliver",
        "description": "My order ORD-1003 has been out for delivery for over 90 minutes. What is happening?",
        "category": "Delivery",
        "priority": "Medium",
        "status": "In Progress",
        "assigned_team": "Delivery Team",
        "idempotency_key": "auto-ORD-1003-delivery-delay",
    },
    {
        "ticket_id": "TKT-0004",
        "customer_idx": 0,
        "order_id": "ORD-1001",
        "title": "Wrong items delivered",
        "description": "I received the wrong order. I ordered Margherita Pizza but received Pepperoni.",
        "category": "Order",
        "priority": "High",
        "status": "Resolved",
        "assigned_team": "Support Team",
        "idempotency_key": "auto-ORD-1001-wrong-items",
    },
    {
        "ticket_id": "TKT-0005",
        "customer_idx": 1,
        "order_id": None,
        "title": "App keeps crashing on payment page",
        "description": "Every time I try to pay through the app, it crashes and closes.",
        "category": "Technical",
        "priority": "Low",
        "status": "Open",
        "assigned_team": "Tech Team",
        "idempotency_key": "manual-app-crash-bob",
    },
]

KNOWLEDGE_DOCS = [
    {
        "doc_id": "faq-001",
        "title": "General FAQ — Ordering & Delivery",
        "category": "FAQ",
        "source": "Restaurant Operations Manual v2.1",
        "content": """# Frequently Asked Questions

## How do I place an order?
You can place an order through our app or website. Browse the menu, add items to your cart, and proceed to checkout. You will receive an order confirmation via email and SMS.

## What are your operating hours?
We are open Monday to Sunday, 10:00 AM to 10:00 PM. Kitchen closes at 9:30 PM for last orders.

## Do you accept online payments?
Yes, we accept all major debit/credit cards, UPI, and digital wallets including Google Pay, Apple Pay, and PayPal.

## How long does delivery take?
Standard delivery time is 30-45 minutes depending on your location and order volume. During peak hours (12-2 PM and 7-9 PM), it may take up to 60 minutes.

## Is there a minimum order amount?
Yes, the minimum order for delivery is $10. There is no minimum for pickup orders.

## Can I track my order?
Yes. Once your order is confirmed, you will receive a tracking link via SMS. You can also track your order in the app under "My Orders".

## Do you offer vegetarian and vegan options?
Yes, we have a wide selection of vegetarian and vegan items. Look for the 🌱 symbol on our menu.

## What if I have dietary allergies?
Please mention any allergies in the order notes. However, we cannot guarantee a 100% allergen-free environment as we prepare food in a shared kitchen.
""",
    },
    {
        "doc_id": "policy-cancel-refund",
        "title": "Cancellation and Refund Policy",
        "category": "Policy",
        "source": "Restaurant Policy Document v3.0",
        "content": """# Cancellation and Refund Policy

## Order Cancellation

### Before Restaurant Accepts (Pending Status)
You may cancel your order without any penalty within 5 minutes of placing it. Full refund will be processed within 5-7 business days.

### After Restaurant Accepts (Confirmed/Preparing Status)
Once the restaurant has accepted and started preparing your order, cancellation is NOT possible. In exceptional cases, contact our support team immediately. Refunds are at management discretion.

### Out for Delivery
Orders that are out for delivery cannot be cancelled.

## Refund Policy

### Full Refunds are issued for:
- Orders cancelled before restaurant acceptance
- Failed payment with successful deduction (processed within 3-5 business days)
- Wrong items delivered (full or partial refund after investigation)
- Items not delivered (full refund after delivery partner confirmation)

### Partial Refunds are issued for:
- Missing items in delivered order
- Quality issues with individual items

### No Refunds for:
- Change of mind after restaurant has started preparation
- Incorrect delivery address provided by customer

## Refund Processing Time
- Credit/Debit Cards: 5-7 business days
- Digital Wallets: 1-3 business days
- UPI: 1-3 business days

## How to Request a Refund
Contact our support team through the app or raise a support ticket. Provide your order ID, the issue description, and any supporting photos if applicable.
""",
    },
    {
        "doc_id": "policy-delivery",
        "title": "Delivery Policy and Information",
        "category": "Policy",
        "source": "Restaurant Policy Document v3.0",
        "content": """# Delivery Policy

## Delivery Coverage Area
We currently deliver within a 10 km radius of our restaurant. You can check if your address is within our delivery zone on our website or app.

## Delivery Charges
- Orders below $20: $2.99 delivery fee
- Orders $20 and above: Free delivery
- Express delivery (within 20 min): Additional $4.99

## Delivery Partners
We use a combination of in-house delivery staff and third-party delivery partners. All delivery staff undergo background verification.

## Failed Delivery Attempts
If the delivery partner is unable to reach you, they will attempt to call you twice. After two failed attempts, the order may be returned and a refund issued minus the delivery charge.

## Contactless Delivery
We offer contactless delivery. Leave instructions in the order notes for the preferred drop-off location.

## Delivery Issues
If your order is delayed beyond 60 minutes from the promised time, please contact support. You may be eligible for a discount voucher.

## Order Not Received
If you have not received your order but the status shows "Delivered", contact us within 24 hours with your order ID. We will investigate with our delivery team.
""",
    },
    {
        "doc_id": "policy-payment",
        "title": "Payment Policy",
        "category": "Policy",
        "source": "Restaurant Policy Document v3.0",
        "content": """# Payment Policy

## Accepted Payment Methods
- Visa, Mastercard, American Express (Debit/Credit)
- UPI (Google Pay, PhonePe, Paytm)
- Apple Pay and Google Pay
- PayPal
- Cash on Delivery (COD) — available for orders under $50

## Payment Security
All online payments are processed through a PCI-DSS compliant payment gateway. We do not store your full card details.

## Payment Failure
If your payment fails:
1. Check if the amount was deducted from your account.
2. If deducted but order shows failed — this is a payment gateway error. The amount will be automatically reversed within 3-5 business days. If not received, raise a support ticket.
3. If not deducted — your order was not placed. Please try again.

## Double Charging
If you believe you have been charged twice for the same order, contact support immediately with both transaction references. We will investigate and process a refund for the duplicate charge within 3 business days.

## Cash on Delivery
COD is available for verified customers only. Please have the exact amount ready. Our delivery staff do not carry change for amounts above $5.
""",
    },
    {
        "doc_id": "faq-complaints",
        "title": "Complaints and Support FAQ",
        "category": "FAQ",
        "source": "Customer Support Guide v1.5",
        "content": """# Complaints and Support

## How do I file a complaint?
You can file a complaint through:
1. The in-app support chat
2. Our website contact form
3. Email: support@restaurant.ai
4. Phone: +1-555-SUPPORT (Monday-Friday 9 AM to 6 PM)

## What happens after I file a complaint?
You will receive a ticket ID immediately. Our support team will review your complaint within 2 business hours during working hours. You will be updated via email on any status changes.

## Priority Levels
- **High Priority**: Payment issues, failed orders with charges, serious food safety concerns. Response within 1 hour.
- **Medium Priority**: Delivery delays, wrong items, quality issues. Response within 4 hours.
- **Low Priority**: General inquiries, feedback, app issues. Response within 24 hours.

## Escalation
If you are not satisfied with the resolution, you can request escalation by replying to the ticket email. Escalated tickets are reviewed by senior management.

## What information should I provide?
- Your order ID (e.g., ORD-1005)
- Date and time of the order
- A clear description of the issue
- Any relevant photos (for wrong/damaged items)
- Your preferred resolution (refund, replacement, etc.)
""",
    },
]


def seed_database(db: Session, force: bool = False) -> dict:
    """Seed the database with sample data. Idempotent — won't duplicate."""
    results = {
        "admin_users": 0,
        "customers": 0,
        "orders": 0,
        "tickets": 0,
        "knowledge_docs": 0,
        "skipped": 0,
    }

    # Seed admin user
    existing_admin = db.query(AdminUser).filter(AdminUser.email == settings.ADMIN_EMAIL).first()
    if not existing_admin:
        admin = AdminUser(
            email=settings.ADMIN_EMAIL,
            name=settings.ADMIN_NAME,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            role="admin",
        )
        db.add(admin)
        results["admin_users"] += 1
    else:
        results["skipped"] += 1

    # Seed customers
    customers_map = {}
    for cdata in SAMPLE_CUSTOMERS:
        existing = db.query(Customer).filter(Customer.email == cdata["email"]).first()
        if not existing:
            cust = Customer(**cdata)
            db.add(cust)
            db.flush()
            customers_map[cdata["email"]] = cust
            results["customers"] += 1
        else:
            customers_map[cdata["email"]] = existing
            results["skipped"] += 1

    db.flush()

    # Seed orders
    customer_list = [db.query(Customer).filter(Customer.email == c["email"]).first() for c in SAMPLE_CUSTOMERS]
    orders_map = {}
    for odata in SAMPLE_ORDERS:
        existing = db.query(Order).filter(Order.order_id == odata["order_id"]).first()
        if not existing:
            customer = customer_list[odata["customer_idx"]]
            items = odata["items"]
            subtotal = sum(i["quantity"] * i["unit_price"] for i in items)
            tax = round(subtotal * 0.1, 2)
            grand_total = round(subtotal + tax, 2)
            created_at = utcnow() - timedelta(days=odata["days_ago"])

            order = Order(
                order_id=odata["order_id"],
                customer_id=customer.id,
                status=odata["status"],
                subtotal=round(subtotal, 2),
                tax=tax,
                grand_total=grand_total,
                notes=odata.get("notes", ""),
                created_at=created_at,
                updated_at=created_at,
            )
            db.add(order)
            db.flush()

            for item in items:
                oi = OrderItem(
                    order_id=order.id,
                    name=item["name"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    total_price=round(item["quantity"] * item["unit_price"], 2),
                )
                db.add(oi)

            orders_map[odata["order_id"]] = order
            results["orders"] += 1
        else:
            orders_map[odata["order_id"]] = existing
            results["skipped"] += 1

    db.flush()

    # Seed support tickets
    for tdata in SAMPLE_TICKETS:
        existing = db.query(SupportTicket).filter(SupportTicket.ticket_id == tdata["ticket_id"]).first()
        if not existing:
            customer = customer_list[tdata["customer_idx"]]
            order = orders_map.get(tdata["order_id"]) if tdata["order_id"] else None
            ticket = SupportTicket(
                ticket_id=tdata["ticket_id"],
                customer_id=customer.id,
                order_id=order.id if order else None,
                title=tdata["title"],
                description=tdata["description"],
                category=tdata["category"],
                priority=tdata["priority"],
                status=tdata["status"],
                assigned_team=tdata["assigned_team"],
                idempotency_key=tdata["idempotency_key"],
                resolved_at=utcnow() if tdata["status"] == "Resolved" else None,
            )
            db.add(ticket)
            db.flush()

            # Add initial timeline entry
            tl = TicketTimeline(
                ticket_id=ticket.id,
                actor="System",
                action="Ticket created",
                details=f"Ticket {tdata['ticket_id']} created with priority {tdata['priority']}",
            )
            db.add(tl)

            if tdata["status"] in ("In Progress", "Resolved", "Escalated"):
                tl2 = TicketTimeline(
                    ticket_id=ticket.id,
                    actor="Support Agent",
                    action="Status updated",
                    details=f"Status changed to {tdata['status']}",
                )
                db.add(tl2)

            results["tickets"] += 1
        else:
            results["skipped"] += 1

    # Seed knowledge documents
    for kdata in KNOWLEDGE_DOCS:
        existing = db.query(KnowledgeDocument).filter(KnowledgeDocument.doc_id == kdata["doc_id"]).first()
        if not existing:
            doc = KnowledgeDocument(**kdata, is_indexed=False)
            db.add(doc)
            results["knowledge_docs"] += 1
        else:
            results["skipped"] += 1

    db.commit()
    return results
