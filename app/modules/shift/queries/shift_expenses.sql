SELECT gtp.gastotipo AS gasto, SUM(gt.valor) AS total
FROM gasto_turno gt
INNER JOIN gasto_tipo gtp ON gtp.idgastotipo = gt.idgastotipo
WHERE gt.idturno = ?
GROUP BY gtp.gastotipo
