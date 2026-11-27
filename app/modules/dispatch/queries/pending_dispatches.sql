SELECT CheckVentasEstacion.IdVentaEstacion, CheckVentasEstacion.FormaPago,
       Venta.Fecha, Venta.CodigoCara, Venta.IdentificacionCliente, Venta.NombreCliente,
       Venta.ValorVenta, Venta.VolumenVenta, Venta.ValorUnitario, Venta.CodigoManguera, Venta.Placa
FROM dbo.FacturaCliente
RIGHT OUTER JOIN dbo.CheckVentasEstacion
  ON CheckVentasEstacion.IdVentaEstacion = FacturaCliente.IdVentaEstacion
 AND FacturaCliente.IdTurno = CheckVentasEstacion.IdTurno
INNER JOIN dbo.Venta
  ON Venta.IdTurno = CheckVentasEstacion.IdTurno
 AND Venta.CodigoVenta = CheckVentasEstacion.IdVentaEstacion
WHERE CheckVentasEstacion.IdTurno = ?
  AND CheckVentasEstacion.aplicaBonoPremio = 1
  AND FacturaCliente.IdDocumento IS NULL
  AND Venta.Estado = 'Finalizada'
  AND (CAST(? AS INT) IS NULL OR Venta.CodigoCara = ?)
ORDER BY CheckVentasEstacion.IdVentaEstacion DESC;
