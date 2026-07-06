/*
    Olist E-Commerce Intelligence Platform
    Fact table DDL for Azure Synapse Analytics dedicated SQL pool.

    Design notes:
    - Facts use surrogate foreign keys to conformed dimensions.
    - Facts retain selected degenerate business identifiers for traceability.
    - Clustered columnstore indexes optimize large analytic scans.
    - Hash distribution on CustomerKey supports common customer, geography,
      cohort, and sales-analysis query patterns.
    - Logical foreign keys are documented in warehouse_design.md and comments
      because dedicated SQL pool does not enforce relational foreign keys.
*/

CREATE TABLE dw.FactSales
(
    SalesKey BIGINT NOT NULL,
    OrderId NVARCHAR(50) NOT NULL,
    OrderItemId INT NOT NULL,
    CustomerKey BIGINT NOT NULL,
    ProductKey BIGINT NOT NULL,
    SellerKey BIGINT NOT NULL,
    OrderPurchaseDateKey INT NOT NULL,
    OrderApprovedDateKey INT NULL,
    OrderStatus NVARCHAR(50) NOT NULL,
    Quantity INT NOT NULL,
    ItemPriceAmount DECIMAL(18,2) NOT NULL,
    FreightAmount DECIMAL(18,2) NOT NULL,
    GrossSalesAmount DECIMAL(18,2) NOT NULL,
    TotalItemAmount DECIMAL(18,2) NOT NULL,
    CreatedAt DATETIME2(3) NOT NULL,
    UpdatedAt DATETIME2(3) NULL
)
WITH
(
    DISTRIBUTION = HASH(CustomerKey),
    CLUSTERED COLUMNSTORE INDEX
);
GO

ALTER TABLE dw.FactSales
ADD CONSTRAINT PK_FactSales
PRIMARY KEY NONCLUSTERED (SalesKey) NOT ENFORCED;
GO

-- Logical FK: FactSales.CustomerKey -> DimCustomer.CustomerKey
-- Logical FK: FactSales.ProductKey -> DimProduct.ProductKey
-- Logical FK: FactSales.SellerKey -> DimSeller.SellerKey
-- Logical FK: FactSales.OrderPurchaseDateKey -> DimDate.DateKey
-- Logical FK: FactSales.OrderApprovedDateKey -> DimDate.DateKey

CREATE TABLE dw.FactPayments
(
    PaymentKey BIGINT NOT NULL,
    OrderId NVARCHAR(50) NOT NULL,
    PaymentSequence INT NOT NULL,
    CustomerKey BIGINT NOT NULL,
    PaymentTypeKey INT NOT NULL,
    OrderPurchaseDateKey INT NOT NULL,
    PaymentInstallments INT NULL,
    PaymentValueAmount DECIMAL(18,2) NOT NULL,
    CreatedAt DATETIME2(3) NOT NULL,
    UpdatedAt DATETIME2(3) NULL
)
WITH
(
    DISTRIBUTION = HASH(CustomerKey),
    CLUSTERED COLUMNSTORE INDEX
);
GO

ALTER TABLE dw.FactPayments
ADD CONSTRAINT PK_FactPayments
PRIMARY KEY NONCLUSTERED (PaymentKey) NOT ENFORCED;
GO

-- Logical FK: FactPayments.CustomerKey -> DimCustomer.CustomerKey
-- Logical FK: FactPayments.PaymentTypeKey -> DimPaymentType.PaymentTypeKey
-- Logical FK: FactPayments.OrderPurchaseDateKey -> DimDate.DateKey

CREATE TABLE dw.FactDelivery
(
    DeliveryKey BIGINT NOT NULL,
    OrderId NVARCHAR(50) NOT NULL,
    CustomerKey BIGINT NOT NULL,
    CustomerGeographyKey BIGINT NULL,
    OrderPurchaseDateKey INT NOT NULL,
    OrderApprovedDateKey INT NULL,
    CarrierDeliveredDateKey INT NULL,
    CustomerDeliveredDateKey INT NULL,
    EstimatedDeliveryDateKey INT NULL,
    OrderStatus NVARCHAR(50) NOT NULL,
    DaysToCarrier INT NULL,
    DaysToCustomer INT NULL,
    EstimatedDeliveryDays INT NULL,
    DeliveryDelayDays INT NULL,
    IsDelivered BIT NOT NULL,
    IsLateDelivery BIT NULL,
    CreatedAt DATETIME2(3) NOT NULL,
    UpdatedAt DATETIME2(3) NULL
)
WITH
(
    DISTRIBUTION = HASH(CustomerKey),
    CLUSTERED COLUMNSTORE INDEX
);
GO

ALTER TABLE dw.FactDelivery
ADD CONSTRAINT PK_FactDelivery
PRIMARY KEY NONCLUSTERED (DeliveryKey) NOT ENFORCED;
GO

-- Logical FK: FactDelivery.CustomerKey -> DimCustomer.CustomerKey
-- Logical FK: FactDelivery.CustomerGeographyKey -> DimGeography.GeographyKey
-- Logical FK: FactDelivery.OrderPurchaseDateKey -> DimDate.DateKey
-- Logical FK: FactDelivery.OrderApprovedDateKey -> DimDate.DateKey
-- Logical FK: FactDelivery.CarrierDeliveredDateKey -> DimDate.DateKey
-- Logical FK: FactDelivery.CustomerDeliveredDateKey -> DimDate.DateKey
-- Logical FK: FactDelivery.EstimatedDeliveryDateKey -> DimDate.DateKey
