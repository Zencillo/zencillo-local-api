DECLARE @Key varchar(100) = ?, @Value varchar(max) = ?;
IF EXISTS (SELECT 1 FROM dbo.ConfiguracionCapturador WITH (UPDLOCK, HOLDLOCK) WHERE Llave = @Key)
    UPDATE dbo.ConfiguracionCapturador SET Valor = @Value WHERE Llave = @Key;
ELSE
    INSERT INTO dbo.ConfiguracionCapturador (Llave, Valor) VALUES (@Key, @Value);
