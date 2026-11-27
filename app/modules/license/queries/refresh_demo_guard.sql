IF NOT EXISTS (
    SELECT 1 FROM sys.dm_exec_connections
    WHERE session_id = @@SPID AND local_net_address = '10.1.10.15'
      AND local_tcp_port = 1433 AND encrypt_option = 'TRUE'
      AND DB_NAME() = 'ZencilloAutomatizacion'
) THROW 50001, 'Destino SQL fuera del piloto autorizado', 1;
