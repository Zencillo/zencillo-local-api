SELECT idpredespachocliente, bono_premio, cara, identificacion, nombre, estado,
       fechacreacion, fechamodificacion, idturno, ISNULL(descuento, 0) AS descuento
FROM dbo.predespacho_cliente WITH (NOLOCK)
WHERE estado = 0
ORDER BY fechacreacion DESC;
