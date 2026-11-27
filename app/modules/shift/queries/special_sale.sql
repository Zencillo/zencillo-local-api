SELECT
        ISNULL(SUM(FC.Subtotal), 0) AS VentaEspecial
    FROM FacturaCliente AS FC
    WHERE FC.IdTurno = ?
      AND ISNULL(FC.precio_especial, 0) = 1
      AND FC.TipoVenta = 1;
