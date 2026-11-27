IF OBJECT_ID(N'dbo.sp_ValorCanjeUltimaVenta', N'P') IS NOT NULL DROP
PROCEDURE dbo.sp_ValorCanjeUltimaVenta;

GO CREATE
PROCEDURE dbo.sp_ValorCanjeUltimaVenta @CodigoCara INT
WITH ENCRYPTION
AS BEGIN
SET
NOCOUNT ON;

SELECT
    TOP 1 V.TipoPreset,
    V.ValorAutorizado,
    V.ValorVenta,
    V.ValorUnitario,
    V.VolumenVenta,
    FC.Facturada,
    FC.IdFacturaCliente,
    CASE
        WHEN V.TipoPreset <= 0 THEN V.ValorAutorizado - V.ValorVenta
        ELSE (V.ValorAutorizado * V.ValorUnitario) - V.ValorVenta
    END AS Cambio
FROM
    dbo.Venta AS V
WITH
    (NOLOCK)
    LEFT JOIN dbo.FacturaCliente AS FC
WITH
    (NOLOCK) ON FC.IdVentaEstacion = V.CodigoVenta
WHERE
    V.CodigoCara = @CodigoCara
    AND V.Estado = 'Finalizada'
ORDER BY
    V.IdVenta DESC;

END;

GO