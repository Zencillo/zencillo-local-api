SELECT BolsasTurno.IdTurno AS IdTurno,
       BolsasTurno.CodigoBolsa AS CodigoBolsa,
       BolsasTurno.ValorBillete AS ValorBillete,
       BolsasTurno.ValorMoneda AS ValorMoneda,
       BolsasTurno.Nota AS Nota
FROM BolsasTurno WITH(NOLOCK)
WHERE BolsasTurno.IdTurno = ?
ORDER BY CodigoBolsa ASC
