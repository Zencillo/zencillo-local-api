IF EXISTS (
    SELECT
        1
    FROM
        dbo.ConfiguracionCapturador
    WHERE
        Llave = 'SIMULAR_REVERSO'
) BEGIN
UPDATE dbo.ConfiguracionCapturador
SET
    Valor = '0'
WHERE
    Llave = 'SIMULAR_REVERSO';

END ELSE BEGIN
INSERT INTO
    dbo.ConfiguracionCapturador (Llave, Valor)
VALUES
    ('SIMULAR_REVERSO', '0');

END;