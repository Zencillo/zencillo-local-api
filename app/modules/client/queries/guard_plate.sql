IF (SELECT COUNT_BIG(*) FROM dbo.ClientePlacaOffLine WITH(UPDLOCK,HOLDLOCK) WHERE Placa=? AND Placa<>'') > 1
    RAISERROR ('La placa tiene varias filas y requiere conciliacion',16,1);
