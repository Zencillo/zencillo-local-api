DECLARE @ManejaZeta bit = ?, @ZetaAutomatica bit = ?, @ManejaConsola bit = ?,
        @HoraInicio varchar(32) = ?, @HoraFin varchar(32) = ?;
IF EXISTS (SELECT 1 FROM dbo.ConfiguracionGeneral WITH (UPDLOCK, HOLDLOCK))
    UPDATE dbo.ConfiguracionGeneral
    SET ManejaZeta = @ManejaZeta, ZetaAutomatica = @ZetaAutomatica,
        ManejaConsola = @ManejaConsola, HoraInicioZetaAutomatica = @HoraInicio,
        HoraFinZetaAutomatica = @HoraFin;
ELSE
    INSERT INTO dbo.ConfiguracionGeneral
        (ManejaZeta, ZetaAutomatica, ManejaConsola, HoraInicioZetaAutomatica, HoraFinZetaAutomatica)
    VALUES (@ManejaZeta, @ZetaAutomatica, @ManejaConsola, @HoraInicio, @HoraFin);
