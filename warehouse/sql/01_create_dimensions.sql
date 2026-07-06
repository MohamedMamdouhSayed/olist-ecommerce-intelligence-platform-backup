/*
    Olist E-Commerce Intelligence Platform
    Dimension table DDL for Azure Synapse Analytics dedicated SQL pool.

    Design notes:
    - Surrogate keys are generated upstream by dbt/ELT processes.
    - Dimensions are REPLICATE distributed to optimize star-schema joins.
    - Primary keys are declared as NOT ENFORCED because Synapse stores them as
      metadata for optimizers and BI tools rather than enforcing row validation.
    - Logical foreign keys are documented in warehouse_design.md and comments
      because dedicated SQL pool does not enforce relational foreign keys.
*/

CREATE TABLE dw.DimDate
(
    DateKey INT NOT NULL,
    FullDate DATE NOT NULL,
    DayNumberOfWeek TINYINT NOT NULL,
    DayName NVARCHAR(20) NOT NULL,
    DayNumberOfMonth TINYINT NOT NULL,
    DayNumberOfYear SMALLINT NOT NULL,
    WeekNumberOfYear TINYINT NOT NULL,
    MonthNumber TINYINT NOT NULL,
    MonthName NVARCHAR(20) NOT NULL,
    CalendarQuarter TINYINT NOT NULL,
    CalendarYear SMALLINT NOT NULL,
    YearMonth CHAR(7) NOT NULL,
    IsWeekend BIT NOT NULL,
    CreatedAt DATETIME2(3) NOT NULL
)
WITH
(
    DISTRIBUTION = REPLICATE,
    HEAP
);
GO

ALTER TABLE dw.DimDate
ADD CONSTRAINT PK_DimDate
PRIMARY KEY NONCLUSTERED (DateKey) NOT ENFORCED;
GO

CREATE TABLE dw.DimGeography
(
    GeographyKey BIGINT NOT NULL,
    ZipCodePrefix NVARCHAR(20) NULL,
    City NVARCHAR(150) NULL,
    StateCode CHAR(2) NULL,
    StateName NVARCHAR(100) NULL,
    CountryCode CHAR(2) NOT NULL,
    CountryName NVARCHAR(100) NOT NULL,
    Latitude DECIMAL(9,6) NULL,
    Longitude DECIMAL(9,6) NULL,
    EffectiveStartDate DATETIME2(3) NOT NULL,
    EffectiveEndDate DATETIME2(3) NULL,
    IsCurrent BIT NOT NULL,
    SourceSystem NVARCHAR(50) NOT NULL,
    CreatedAt DATETIME2(3) NOT NULL,
    UpdatedAt DATETIME2(3) NULL
)
WITH
(
    DISTRIBUTION = REPLICATE,
    HEAP
);
GO

ALTER TABLE dw.DimGeography
ADD CONSTRAINT PK_DimGeography
PRIMARY KEY NONCLUSTERED (GeographyKey) NOT ENFORCED;
GO

CREATE TABLE dw.DimCustomer
(
    CustomerKey BIGINT NOT NULL,
    CustomerId NVARCHAR(50) NOT NULL,
    CustomerUniqueId NVARCHAR(50) NULL,
    CustomerGeographyKey BIGINT NULL,
    CustomerCity NVARCHAR(150) NULL,
    CustomerState CHAR(2) NULL,
    CustomerZipCodePrefix NVARCHAR(20) NULL,
    EffectiveStartDate DATETIME2(3) NOT NULL,
    EffectiveEndDate DATETIME2(3) NULL,
    IsCurrent BIT NOT NULL,
    SourceSystem NVARCHAR(50) NOT NULL,
    CreatedAt DATETIME2(3) NOT NULL,
    UpdatedAt DATETIME2(3) NULL
)
WITH
(
    DISTRIBUTION = REPLICATE,
    HEAP
);
GO

ALTER TABLE dw.DimCustomer
ADD CONSTRAINT PK_DimCustomer
PRIMARY KEY NONCLUSTERED (CustomerKey) NOT ENFORCED;
GO

-- Logical FK: DimCustomer.CustomerGeographyKey -> DimGeography.GeographyKey

CREATE TABLE dw.DimProduct
(
    ProductKey BIGINT NOT NULL,
    ProductId NVARCHAR(50) NOT NULL,
    ProductCategoryName NVARCHAR(150) NULL,
    ProductCategoryNameEnglish NVARCHAR(150) NULL,
    ProductNameLength INT NULL,
    ProductDescriptionLength INT NULL,
    ProductPhotosQty INT NULL,
    ProductWeightGrams DECIMAL(18,4) NULL,
    ProductLengthCm DECIMAL(18,4) NULL,
    ProductHeightCm DECIMAL(18,4) NULL,
    ProductWidthCm DECIMAL(18,4) NULL,
    EffectiveStartDate DATETIME2(3) NOT NULL,
    EffectiveEndDate DATETIME2(3) NULL,
    IsCurrent BIT NOT NULL,
    SourceSystem NVARCHAR(50) NOT NULL,
    CreatedAt DATETIME2(3) NOT NULL,
    UpdatedAt DATETIME2(3) NULL
)
WITH
(
    DISTRIBUTION = REPLICATE,
    HEAP
);
GO

ALTER TABLE dw.DimProduct
ADD CONSTRAINT PK_DimProduct
PRIMARY KEY NONCLUSTERED (ProductKey) NOT ENFORCED;
GO

CREATE TABLE dw.DimSeller
(
    SellerKey BIGINT NOT NULL,
    SellerId NVARCHAR(50) NOT NULL,
    SellerGeographyKey BIGINT NULL,
    SellerCity NVARCHAR(150) NULL,
    SellerState CHAR(2) NULL,
    SellerZipCodePrefix NVARCHAR(20) NULL,
    EffectiveStartDate DATETIME2(3) NOT NULL,
    EffectiveEndDate DATETIME2(3) NULL,
    IsCurrent BIT NOT NULL,
    SourceSystem NVARCHAR(50) NOT NULL,
    CreatedAt DATETIME2(3) NOT NULL,
    UpdatedAt DATETIME2(3) NULL
)
WITH
(
    DISTRIBUTION = REPLICATE,
    HEAP
);
GO

ALTER TABLE dw.DimSeller
ADD CONSTRAINT PK_DimSeller
PRIMARY KEY NONCLUSTERED (SellerKey) NOT ENFORCED;
GO

-- Logical FK: DimSeller.SellerGeographyKey -> DimGeography.GeographyKey

CREATE TABLE dw.DimPaymentType
(
    PaymentTypeKey INT NOT NULL,
    PaymentTypeCode NVARCHAR(50) NOT NULL,
    PaymentTypeName NVARCHAR(100) NOT NULL,
    PaymentCategory NVARCHAR(100) NULL,
    IsDigitalPayment BIT NULL,
    CreatedAt DATETIME2(3) NOT NULL,
    UpdatedAt DATETIME2(3) NULL
)
WITH
(
    DISTRIBUTION = REPLICATE,
    HEAP
);
GO

ALTER TABLE dw.DimPaymentType
ADD CONSTRAINT PK_DimPaymentType
PRIMARY KEY NONCLUSTERED (PaymentTypeKey) NOT ENFORCED;
GO
