SELECT
  id,
  ip,
  mascara,
  gateway,
  hostPrinciR1Ip,
  hostPrinciR1Puerto,
  hostAlterR1Ip,
  hostAlterR1Puerto,
  hostPrinciR2Ip,
  hostPrinciR2Puerto,
  hostAlterR2Ip,
  hostAlterR2Puerto,
  puertoEscucha
FROM ConfiguracionMediaNet
WHERE id = 1;
