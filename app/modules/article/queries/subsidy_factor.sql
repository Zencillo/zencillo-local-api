DECLARE @Article varchar(100) = ?;
SELECT 
    [IdArticulo],
    [SubsidioFactor],
    [Ano],
    [Mes]
FROM SubsidioEcuador
WHERE [IdArticulo] = 
    CASE 
        WHEN @Article NOT LIKE '%[^0-9]%' AND @Article <> ''
            THEN CONVERT(INT, @Article)
        ELSE 0
    END
AND [Ano] = ?
AND [Mes] = ?
