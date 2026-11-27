DECLARE @Config XML = CONVERT(XML, ?);
EXEC dbo.sp_InsertarActualizarConfigCapturador_LlaveValorXML @XmlConfig = @Config;
