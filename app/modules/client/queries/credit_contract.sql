SELECT TOP 1
  [idcontratocredito],
  [idcliente],
  [identificacion],
  [cliente],
  [fechainicio],
  [fechafin],
  [descripcion],
  [numero]
FROM [dbo].[contrato_credito] WITH (NOLOCK)
WHERE REPLACE(REPLACE(REPLACE(LTRIM(RTRIM([identificacion])), '-', ''), ' ', ''), '.', '') = ?
