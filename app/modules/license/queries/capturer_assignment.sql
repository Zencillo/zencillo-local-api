SELECT [IdCapturadorCaras], [IdIsla], [NumeroCapturador], [Puerto], [IP]
FROM [dbo].[CapturadorCaras] WITH(NOLOCK)
WHERE [IdIsla] = ? AND [NumeroCapturador] = ?;
