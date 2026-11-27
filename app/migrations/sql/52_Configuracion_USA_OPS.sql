IF NOT EXISTS (
    SELECT
        1
    FROM
        dbo.ConfiguracionCapturador
    WHERE
        Llave = 'USA_OPS'
) BEGIN
INSERT INTO
    dbo.ConfiguracionCapturador (Llave, Valor)
VALUES
    ('USA_OPS', '0');

END;
