-- Generado a partir del script suministrado.
-- Ejecutar respetando el numero del archivo.
SET
NOCOUNT ON;

--delete sp 'FacturacionRDComplete'
IF EXISTS (
	SELECT
		1
	FROM
		sysobjects
	WHERE
		name = 'FacturacionRDComplete'
		AND
	TYPE = 'P'
) BEGIN DROP PROC FacturacionRDComplete END
--delete spInvoiceGTM
IF EXISTS (
	SELECT
		1
	FROM
		sysobjects
	WHERE
		name = 'spInvoiceGTM'
		AND
	TYPE = 'P'
) BEGIN DROP PROC spInvoiceGTM END
--delete sp InvoiceFastConversion
IF EXISTS (
	SELECT
		1
	FROM
		sysobjects
	WHERE
		name = 'InvoiceFastConversion'
		AND
	TYPE = 'P'
) BEGIN DROP PROC InvoiceFastConversion END
--delete sp InvoiceFast
IF EXISTS (
	SELECT
		1
	FROM
		sysobjects
	WHERE
		name = 'InvoiceFast'
		AND
	TYPE = 'P'
) BEGIN DROP PROC InvoiceFast END
--delete IX_VentasCupo IN VentasCupo
IF EXISTS (
	SELECT
		*
	FROM
		sys.indexes
	WHERE
		OBJECT_ID = OBJECT_ID(N'[dbo].[VentasCupo]')
		AND name = N'IX_VentasCupo'
) BEGIN DROP
INDEX [IX_VentasCupo] ON [dbo].[VentasCupo] END IF EXISTS (
	SELECT
		1
	FROM
		sysobjects
	WHERE
		name = 'spAddLogAuditoriaContingencia'
		AND
	TYPE = 'P'
) BEGIN DROP PROC spAddLogAuditoriaContingencia END IF EXISTS (
	SELECT
		1
	FROM
		sysobjects
	WHERE
		name = 'spObtenerNumeroFactura'
		AND
	TYPE = 'P'
) BEGIN DROP PROC spObtenerNumeroFactura END