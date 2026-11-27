SELECT art.CodigoArticulo, art.Articulo, art.NombreCorto, art_inv.saldo
FROM articuloexistencia_pv AS art_inv
INNER JOIN Articulo AS art ON art.IdArticulo = art_inv.idarticulo
WHERE art_inv.idpuntoventa = ? AND art.Estado = 1 AND art.Combustible = 0
