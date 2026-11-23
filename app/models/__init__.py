"""Importing this package registers every table on Base.metadata."""
from app.models.agent import AgentMessage, AgentRun, AgentRunEvent, AgentSession, AgentToolCall
from app.models.catalog import (
    Brand,
    FulfillmentRate,
    GrapeVariety,
    InventoryLevel,
    Product,
    ProductAccolade,
    ProductGrape,
    ProductListing,
    ProductPrice,
    ProductVariant,
    Promotion,
    Region,
    VariantCertification,
    VariantNutrition,
    WineStyle,
)
from app.models.customer import AgeVerification, Customer, CustomerAddress, CustomerPaymentMethod
from app.models.fulfillment import Shipment, ShipmentItem, ShipmentTrackingEvent
from app.models.order import (
    InventoryReservation,
    Order,
    OrderAddress,
    OrderDiscount,
    OrderItem,
    OrderStatusHistory,
)
from app.models.organization import StaffUser, Store, StoreHours, StoreHoursException, Warehouse
from app.models.payment import (
    GiftCard,
    GiftCardTransaction,
    LoyaltyAccount,
    LoyaltyPointTransaction,
    LoyaltyReward,
    Payment,
    PaymentTransaction,
    StoreCreditTransaction,
)
from app.models.returns import Refund, RefundItem, ReturnEvidence, ReturnItem, ReturnRequest
from app.models.support import AuditLog, IdempotencyRecord, SupportTicket, TicketMessage

__all__ = [
    "AgeVerification", "AgentMessage", "AgentRun", "AgentRunEvent", "AgentSession", "AgentToolCall",
    "AuditLog", "Brand", "Customer", "CustomerAddress", "CustomerPaymentMethod", "FulfillmentRate",
    "GiftCard", "GiftCardTransaction", "GrapeVariety", "IdempotencyRecord", "InventoryLevel",
    "InventoryReservation", "LoyaltyAccount", "LoyaltyPointTransaction", "LoyaltyReward", "Order",
    "OrderAddress", "OrderDiscount", "OrderItem", "OrderStatusHistory", "Payment", "PaymentTransaction",
    "Product", "ProductAccolade", "ProductGrape", "ProductListing", "ProductPrice", "ProductVariant",
    "Promotion", "Refund", "RefundItem", "Region", "ReturnEvidence", "ReturnItem", "ReturnRequest",
    "Shipment", "ShipmentItem", "ShipmentTrackingEvent", "StaffUser", "Store", "StoreCreditTransaction",
    "StoreHours", "StoreHoursException", "SupportTicket", "TicketMessage", "VariantCertification",
    "VariantNutrition", "Warehouse", "WineStyle",
]
