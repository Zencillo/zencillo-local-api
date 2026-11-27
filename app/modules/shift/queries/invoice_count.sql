SELECT COUNT(DISTINCT [IdFacturaCliente]) AS Cantidad
FROM [dbo].[FacturaCliente] WITH (NOLOCK)
WHERE [IdTurno] = ?
