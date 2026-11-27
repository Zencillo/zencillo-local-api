UPDATE AEP SET saldo = ISNULL(AEP.saldo, 0) - ?
FROM dbo.articuloexistencia_pv AEP
WHERE AEP.idarticulo = ? AND AEP.idpuntoventa = ?
  AND ? IS NOT NULL AND ? IS NOT NULL AND ? IS NOT NULL AND ? IS NOT NULL;
