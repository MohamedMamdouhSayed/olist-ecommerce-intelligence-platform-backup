/*
    Olist E-Commerce Intelligence Platform
    Azure Synapse Enterprise Data Warehouse Schema

    This script creates the logical schema used by the Gold-to-Warehouse load.
*/

IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = 'dw'
)
BEGIN
    EXEC('CREATE SCHEMA dw');
END;
GO

