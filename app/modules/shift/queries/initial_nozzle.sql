IF NOT EXISTS (SELECT 1 FROM dbo.TurnoEmpleado WHERE IdTurno = ? AND Isla = ?)
BEGIN
    RAISERROR ('Turno no autorizado.', 16, 1);
    RETURN;
END;
EXEC dbo.sp_GuardarTurnoDetalleLecturaInicial @IdTurno = ?, @CodigoManguera = ?, @LecturaInicial = ?, @Precio = ?;
