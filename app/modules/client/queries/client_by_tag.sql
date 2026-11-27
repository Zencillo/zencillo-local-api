SELECT ClientePlacaOffLine.Placa,
ClientePlacaOffLine.Identificador,
ClienteOffLine.Identificacion,
ClienteOffLine.Correo AS 'ClienteCorreo',
ClienteOffLine.NombreCliente,
ClienteOffLine.IdGrupoEmpresarial,
ClienteOffLine.GrupoEmpresarial,
ClienteOffLine.Telefono,
ClienteOffLine.DigVef,
ISNULL(integracion.tipointegracion,0) as tipoIntegracion
FROM PlacaIdentificadorOffline
INNER JOIN ClientePlacaOffLine ON ClientePlacaOffLine.Placa = PlacaIdentificadorOffline.Placa
INNER JOIN ClienteOffLine ON ClienteOffLine.Identificacion = ClientePlacaOffLine.Identificacion
left join
[integracion_cliente] as integracion on ClienteOffLine.Identificacion = integracion.identificacion and integracion.estado = 1
WHERE PlacaIdentificadorOffline.Identificador = ?
