SELECT CVE.IdVentaEstacion, CVE.Cara, CVE.Estado, CVE.IdTurno,
       FC.IdDocumento, V.Estado AS EstadoVenta
FROM dbo.FacturaCliente FC WITH (NOLOCK)
RIGHT JOIN dbo.CheckVentasEstacion CVE WITH (NOLOCK)
  ON CVE.IdVentaEstacion = FC.IdVentaEstacion AND FC.IdTurno = CVE.IdTurno
INNER JOIN dbo.Venta V WITH (NOLOCK) ON CVE.IdVentaEstacion = V.CodigoVenta
INNER JOIN dbo.TurnoEmpleado TE WITH (NOLOCK) ON TE.IdTurno = CVE.IdTurno
WHERE CVE.Cara = ? AND CVE.IdTurno = ? AND FC.IdDocumento IS NULL
  AND CVE.Estado = 0 AND CVE.CodigoIsla = ?
  AND ? IS NOT NULL AND ? IS NOT NULL AND TE.Isla = ?
ORDER BY CVE.IdVentaEstacion DESC;
