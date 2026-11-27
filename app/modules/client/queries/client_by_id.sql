SELECT 
          c.[Identificacion],
          c.[NombreCliente],
          c.[IdGrupoEmpresarial],
          c.[GrupoEmpresarial],
          c.[Telefono],
          c.[Correo] AS [ClienteCorreo],
          c.[DigVef],
          c.[Verificado],
          c.[CodTipo],
          ISNULL(integracion.tipointegracion,0) as tipoIntegracion
        FROM [ClienteOffLine] c
        left join
        [integracion_cliente] as integracion on c.Identificacion = integracion.identificacion and integracion.estado = 1
        WHERE c.[Identificacion] = ?;
