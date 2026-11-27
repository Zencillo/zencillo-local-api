SELECT UsuarioLicencia, ContrasenaLicencia
FROM dbo.ConfiguracionInicial
WHERE IdCompania = ? AND IdCentroVenta = ? AND CodigoIsla = ?;
