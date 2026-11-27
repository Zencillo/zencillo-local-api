IF EXISTS (SELECT 1 FROM dbo.ConfiguracionCapturador WHERE LLAVE = ?)
BEGIN
    UPDATE dbo.ConfiguracionCapturador
    SET VALOR = ?
    WHERE LLAVE = ?;
END
ELSE
BEGIN
    INSERT INTO dbo.ConfiguracionCapturador (LLAVE, VALOR)
    VALUES (?, ?);
END
