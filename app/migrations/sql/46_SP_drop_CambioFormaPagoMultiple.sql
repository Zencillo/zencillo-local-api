-- SQL Server 2008+: elimina SPs del cambio de forma de pago múltiple (revertido a flujo Dart).

IF OBJECT_ID(N'dbo.sp_CambiarFormaPagoFacturaMultiple', N'P') IS NOT NULL
BEGIN
  DROP PROCEDURE dbo.sp_CambiarFormaPagoFacturaMultiple;
END;

IF OBJECT_ID(N'dbo.sp_InsertarFormaPagoDetalleVenta', N'P') IS NOT NULL
BEGIN
  DROP PROCEDURE dbo.sp_InsertarFormaPagoDetalleVenta;
END;

GO
