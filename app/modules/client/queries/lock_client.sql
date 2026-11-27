SELECT Identificacion FROM dbo.ClienteOffLine WITH (UPDLOCK, HOLDLOCK) WHERE Identificacion = ?;
