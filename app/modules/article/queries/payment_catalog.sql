SELECT
    FP.IdFormaPago,
    FDP.FormaPago,
    ISNULL(FP.Codigo, 0) AS Codigo,
    FDP.Activa,
    FP.EnviaDatafono
FROM FormasDePagoPOS AS FDP
LEFT JOIN FormaPago AS FP
    ON REPLACE(REPLACE(FP.Nombre, ' ', ''), '?', 'e') COLLATE Latin1_General_CI_AI =
       REPLACE(REPLACE(FDP.FormaPago, ' ', ''), '?', 'e') COLLATE Latin1_General_CI_AI
WHERE FDP.Activa = 1;
