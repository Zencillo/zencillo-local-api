IF NOT EXISTS (
    SELECT
        1
    FROM
        dbo.ConfiguracionCapturador
    WHERE
        Llave = 'USA_PORTAL_SDK'
) BEGIN
INSERT INTO
    dbo.ConfiguracionCapturador (Llave, Valor)
VALUES
    ('USA_PORTAL_SDK', '0');

END;
